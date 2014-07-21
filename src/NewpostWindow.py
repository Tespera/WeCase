#!/usr/bin/env python3
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

# WeCase -- This file implemented NewpostWindow.
# Copyright (C) 2013, 2014 The WeCase Developers.
# License: GPL v3 or later.


from os.path import getsize
from WeHack import async
from PyQt4 import QtCore, QtGui
from weibo3 import APIError
from Tweet import TweetItem, UserItem, TweetUnderCommentModel, TweetRetweetModel
from Notify import Notify
from TweetUtils import tweetLength
from NewpostWindow_ui import Ui_NewPostWindow
from FaceWindow import FaceWindow
from TweetListWidget import TweetListWidget, SingleTweetWidget
from WeiboErrorHandler import APIErrorWindow
import const


class NewpostWindow(QtGui.QDialog, Ui_NewPostWindow):
    image = None
    apiError = QtCore.pyqtSignal(Exception)
    commonError = QtCore.pyqtSignal(str, str)
    sendSuccessful = QtCore.pyqtSignal()
    userClicked = QtCore.pyqtSignal(UserItem, bool)
    tagClicked = QtCore.pyqtSignal(str, bool)
    tweetRefreshed = QtCore.pyqtSignal()
    tweetRejected = QtCore.pyqtSignal()

    def __init__(self, action="new", tweet=None, parent=None):
        super(NewpostWindow, self).__init__(parent)
        self.setAttribute(QtCore.Qt.WA_QuitOnClose, False)
        self.client = const.client
        self.tweet = tweet
        self.action = action
        self.setupUi(self)
        self.textEdit.callback = self.mentions_suggest
        self.textEdit.mention_flag = "@"
        self.notify = Notify(timeout=1)
        self._sent = False
        self.apiError.connect(self.showException)
        self.sendSuccessful.connect(self.sent)
        self.commonError.connect(self.showErrorMessage)
        self.errorWindow = APIErrorWindow(self)

        if self.action not in ["new", "reply"]:
            self.tweetRefreshed.connect(self._create_tweetWidget)
            self.tweetRejected.connect(lambda: self.pushButton_send.setEnabled(False))
            self._refresh()

    def setupUi(self, widget):
        super(NewpostWindow, self).setupUi(widget)
        self.sendAction = QtGui.QAction(self)
        self.sendAction.triggered.connect(self.send)
        self.sendAction.setShortcut(QtGui.QKeySequence("Ctrl+Return"))
        self.addAction(self.sendAction)

        self.checkChars()
        self.setupButtons()

    def setupButtons(self):
        # Disabled is the default state of buttons
        self.pushButton_picture.setEnabled(False)
        self.chk_repost.setEnabled(False)
        self.chk_comment.setEnabled(False)
        self.chk_comment_original.setEnabled(False)

        if self.action == "new":
            assert (not self.tweet)  # Shouldn't have a tweet object.
            self.pushButton_picture.setEnabled(True)
        elif self.action == "retweet":
            self.chk_comment.setEnabled(True)
            if self.tweet.type == TweetItem.RETWEET:
                self.textEdit.setText(self.tweet.append_existing_replies())
                self.chk_comment_original.setEnabled(True)
        elif self.action == "comment":
            self.chk_repost.setEnabled(True)
            if self.tweet.type == TweetItem.RETWEET:
                self.chk_comment_original.setEnabled(True)
        elif self.action == "reply":
            self.chk_repost.setEnabled(True)
            if self.tweet.original.type == TweetItem.RETWEET:
                self.chk_comment_original.setEnabled(True)
        else:
            assert False

    @async
    def _refresh(self):
        # The read count is not a real-time value. So refresh it now.
        try:
            self.tweet.refresh()
        except APIError as e:
            self.errorWindow.raiseException.emit(e)
            self.tweetRejected.emit()
            return
        self.tweetRefreshed.emit()

    def _create_tweetWidget(self):
        if self.action == "comment" and self.tweet.comments_count:
            self.tweetWidget = SingleTweetWidget(self.tweet, ["image", "original"], self)
            self.replyModel = TweetUnderCommentModel(self.client.api("comments/show"), self.tweet.id, self)
        elif self.action == "retweet" and self.tweet.retweets_count:
            if self.tweet:
                self.tweetWidget = SingleTweetWidget(self.tweet, ["image", "original"], self)
            elif self.tweet.original:
                self.tweetWidget = SingleTweetWidget(self.tweet.original, ["image", "original"], self)
            self.replyModel = TweetRetweetModel(self.client.api("statuses/repost_timeline"), self.tweet.id, self)
        else:
            return
        self.replyModel.load()

        self.splitter = QtGui.QSplitter(self)
        self.splitter.setOrientation(QtCore.Qt.Vertical)
        self.verticalLayout.insertWidget(0, self.splitter)
        self.tweetWidget.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        self.splitter.addWidget(self.tweetWidget)

        self.commentsWidget = TweetListWidget(self, ["image", "original"])
        self.commentsWidget.setModel(self.replyModel)
        self.commentsWidget.scrollArea.setMinimumSize(20, 200)
        self.commentsWidget.userClicked.connect(self.userClicked)
        self.commentsWidget.tagClicked.connect(self.tagClicked)
        self.splitter.addWidget(self.commentsWidget)
        self.splitter.addWidget(self.textEdit)

    def mentions_suggest(self, text):
        ret_users = []
        try:
            word = text.split(' ')[-1]
            word = word.split('@')[-1]
        except IndexError:
            return []
        if not word.strip():
            return []
        users = self.client.api("search/suggestions/at_users").get(q=word, type=0)
        for user in users:
            ret_users.append("@" + user['nickname'])
        return ret_users

    def sent(self):
        self._sent = True
        self.close()

    def send(self):
        self.pushButton_send.setEnabled(False)
        if self.action == "new":
            self.new()
        elif self.action == "retweet":
            self.retweet()
        elif self.action == "comment":
            self.comment()
        elif self.action == "reply":
            self.reply()
        else:
            # If action is in other types, it must be a mistake.
            assert False

    @async
    def retweet(self):
        text = str(self.textEdit.toPlainText())
        comment = int(self.chk_comment.isChecked())
        comment_ori = int(self.chk_comment_original.isChecked())
        try:
            self.tweet.retweet(text, comment, comment_ori)
        except APIError as e:
            self.apiError.emit(e)
            return
        self.notify.showMessage(self.tr("WeCase"), self.tr("Retweet Success!"))
        self.sendSuccessful.emit()

    @async
    def comment(self):
        text = str(self.textEdit.toPlainText())
        retweet = int(self.chk_repost.isChecked())
        comment_ori = int(self.chk_comment_original.isChecked())
        try:
            self.tweet.comment(text, comment_ori, retweet)
        except APIError as e:
            self.apiError.emit(e)
            return
        self.notify.showMessage(self.tr("WeCase"), self.tr("Comment Success!"))
        self.sendSuccessful.emit()

    @async
    def reply(self):
        text = str(self.textEdit.toPlainText())
        comment_ori = int(self.chk_comment_original.isChecked())
        retweet = int(self.chk_repost.isChecked())
        try:
            self.tweet.reply(text, comment_ori, retweet)
        except APIError as e:
            self.apiError.emit(e)
            return
        self.notify.showMessage(self.tr("WeCase"), self.tr("Reply Success!"))
        self.sendSuccessful.emit()

    @async
    def new(self):
        text = str(self.textEdit.toPlainText())

        try:
            if self.image:
                try:
                    if getsize(self.image) > const.MAX_IMAGE_BYTES:
                        raise ValueError
                    with open(self.image, "rb") as image:
                        self.client.api("statuses/upload").post(status=text, pic=image)
                except (OSError, IOError):
                    self.commonError.emit(self.tr("File not found"),
                                          self.tr("No such file: %s")
                                          % self.image)
                    self.addImage()  # In fact, remove image...
                    return
                except ValueError:
                    self.commonError.emit(self.tr("Too large size"),
                                          self.tr("This image is too large to upload: %s")
                                          % self.image)
                    self.addImage()  # In fact, remove image...
                    return
            else:
                self.client.api("statuses/update").post(status=text)

            self.notify.showMessage(self.tr("WeCase"),
                                    self.tr("Tweet Success!"))
            self.sendSuccessful.emit()
        except APIError as e:
            self.apiError.emit(e)
            return

        self.image = None

    def addImage(self):
        ACCEPT_TYPE = self.tr("Images") + "(*.png *.jpg *.jpeg *.bmp *.gif)"
        if self.image:
            self.image = None
            self.pushButton_picture.setText(self.tr("&Picture"))
        else:
            self.image = QtGui.QFileDialog.getOpenFileName(self,
                                                           self.tr("Choose a"
                                                                   " image"),
                                                           filter=ACCEPT_TYPE)
            # user may cancel the dialog, so check again
            if self.image:
                self.pushButton_picture.setText(self.tr("Remove the picture"))
        self.textEdit.setFocus()

    def showException(self, e):
        if "Text too long" in str(e):
            QtGui.QMessageBox.warning(None, self.tr("Text too long!"),
                                      self.tr("Please remove some text."))
        else:
            self.errorWindow.raiseException.emit(e)
        self.pushButton_send.setEnabled(True)

    def showErrorMessage(self, title, text):
        QtGui.QMessageBox.warning(self, title, text)

    def showSmiley(self):
        wecase_smiley = FaceWindow()
        if wecase_smiley.exec_():
            self.textEdit.textCursor().insertText(wecase_smiley.faceName)
        self.textEdit.setFocus()

    def checkChars(self):
        """Check textEdit's characters.
        If it larger than 140, Send Button will be disabled
        and label will show red chars."""

        text = self.textEdit.toPlainText()
        numLens = 140 - tweetLength(text)
        if numLens == 140 and (not self.action == "retweet"):
            # you can not send empty tweet, except retweet
            self.pushButton_send.setEnabled(False)
        elif numLens >= 0:
            # length is okay
            self.label.setStyleSheet("color:black;")
            self.pushButton_send.setEnabled(True)
        else:
            # text is too long
            self.label.setStyleSheet("color:red;")
            self.pushButton_send.setEnabled(False)
        self.label.setText(str(numLens))

    def reject(self):
        self.close()

    def closeEvent(self, event):
        # We have unsend text.
        if (not self._sent) and (self.textEdit.toPlainText()):
            choice = QtGui.QMessageBox.question(
                self, self.tr("Close?"),
                self.tr("All unpost text will lost."),
                QtGui.QMessageBox.Yes,
                QtGui.QMessageBox.No)
            if choice == QtGui.QMessageBox.No:
                event.ignore()
            else:
                self.setParent(None)
