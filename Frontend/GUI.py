from PyQt5.QtWidgets import QApplication, QStackedWidget, QSizePolicy, QMainWindow, QFrame, QTextEdit, QStackedLayout, QWidget, QLineEdit, QGridLayout, QVBoxLayout, QPushButton, QLabel, QHBoxLayout, QGraphicsDropShadowEffect, QFileDialog, QDialog
from PyQt5.QtGui import QIcon, QFont, QPixmap, QPainter, QMovie, QColor, QTextCharFormat, QTextBlockFormat, QTextCursor, QDesktopServices
from PyQt5.QtCore import Qt, QSize, QTimer, QUrl
# from attr import s
from dotenv import dotenv_values
import sys
import os
from Backend.FileContext import register_uploads, remove_upload
import time
# from torch import layout
# from Backend.SpeechToText import TempDirPath

env_vars = dotenv_values(".env")
Username = env_vars.get("Username") or "User"
Assistantname = env_vars.get("Assistantname") or "Lucy"
current_dir = os.getcwd()
old_chat_message = ""
TempDirPath = rf"{current_dir}\Frontend\Files"
GraphicsDirPath = rf"{current_dir}\Frontend\Graphics"
os.makedirs(TempDirPath, exist_ok=True)

APP_BACKGROUND = "#131314"
PANEL_BACKGROUND = "#1E1F20"
PANEL_BACKGROUND_2 = "#252628"
TEXT_PRIMARY = "#E8EAED"
TEXT_MUTED = "#A8A9AD"
ACCENT = "#8AB4F8"
ACCENT_2 = "#FDD663"
BORDER = "#34363A"

def _read_temp_file(filename, default=""):
      try:
            with open(TempDirectoryPath(filename), "r", encoding="utf-8") as file:
                  return file.read()
      except OSError:
            return default


def AnswerModifier(Answer):
      lines = Answer.split('\n')
      non_empty_lines = [line for line in lines if line.strip()]
      modified_answer = '\n'.join(non_empty_lines)
      return modified_answer

def QueryModifier(Query):
       
      new_query = Query.lower().strip()
      if not new_query:
            return ""

      query_words = new_query.split()
      question_words = ["how", "what", "why", "where", "when", "who", "which", "whose", "whom", "can you", "what's", "where's", "how's"]

      if any(word + " " in new_query for word in question_words):
            if query_words[-1][-1] in ['.', '?', '!']:
                  new_query = new_query[:-1] + "?"

            else:
                  new_query += "?"

      else:
            if query_words[-1][-1] in ['.', '?', '!']:
                  new_query = new_query[:-1] + "."
            
            else:
                  new_query += "."

      return new_query.capitalize()

def SetMicrophoneStatus(Command):
      with open(rf'{TempDirPath}\Mic.data', "w", encoding='utf-8') as file:
            file.write(Command)


def GetMicrophoneStatus():
      return _read_temp_file('Mic.data', "False")

def SetAssistantStatus(Status):
      with open (rf'{TempDirPath}\Status.data', "w", encoding='utf-8') as file:
            file.write(Status)

def GetAssistantStatus():
      return _read_temp_file('Status.data', "Available...")

def MicButtonInitiated():
      SetMicrophoneStatus("False")

def MicButtonClosed():
      SetMicrophoneStatus("True")

def GraphicsDirectoryPath(Filename):
      Path = rf'{GraphicsDirPath}\{Filename}'
      return Path

def TempDirectoryPath(Filename):
      Path = rf'{TempDirPath}\{Filename}'
      return Path

def ShowTextToScreen(Text):
      with open(rf'{TempDirPath}\Response.data', "w", encoding='utf-8') as file:
            file.write(Text)

def SendTypedMessage(Text):
      text = str(Text).strip()
      if not text:
            return

      with open(rf'{TempDirPath}\TypedQuery.data', "w", encoding='utf-8') as file:
            file.write(text)

def RequestStopSpeaking():
      with open(rf'{TempDirPath}\Control.data', "w", encoding='utf-8') as file:
            file.write("stop")

def RequestDirectListen():
      with open(rf'{TempDirPath}\Control.data', "w", encoding='utf-8') as file:
            file.write("listen")

def _image_src(path):
      return "file:///" + os.path.abspath(path).replace("\\", "/")

def _read_and_clear_temp_file(filename):
      path = TempDirectoryPath(filename)
      try:
            with open(path, "r", encoding="utf-8") as file:
                  data = file.read().strip()
            if data:
                  with open(path, "w", encoding="utf-8") as file:
                        file.write("")
            return data
      except OSError:
            return ""

def UploadFiles(Parent=None):
      file_paths, _ = QFileDialog.getOpenFileNames(
            Parent,
            "Upload files for context",
            current_dir,
            "Supported files (*.txt *.md *.py *.js *.html *.css *.json *.csv *.tsv *.log *.xml *.yaml *.yml *.ini *.png *.jpg *.jpeg *.webp);;All files (*.*)"
      )
      return register_uploads(file_paths)

class PasteAwareLineEdit(QLineEdit):
      def __init__(self, on_image_paste=None):
            super().__init__()
            self.on_image_paste = on_image_paste

      def paste(self):
            clipboard = QApplication.clipboard()
            mime_data = clipboard.mimeData()

            if mime_data.hasImage():
                  os.makedirs(rf"{current_dir}\TEMP", exist_ok=True)
                  image = clipboard.image()
                  filename = f"clipboard-image-{int(time.time())}.png"
                  path = rf"{current_dir}\TEMP\{filename}"

                  if image.save(path, "PNG"):
                        added = register_uploads([path])
                        if self.on_image_paste:
                              self.on_image_paste(added)
                        return

            super().paste()

class ImageLightbox(QDialog):
      def __init__(self, image_path, parent=None):
            super().__init__(parent)
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
            self.setAttribute(Qt.WA_TranslucentBackground)
            
            # Semi-transparent background overlay matching APP_BACKGROUND style
            self.setStyleSheet("background-color: rgba(10, 10, 12, 0.92);")
            
            layout = QVBoxLayout(self)
            layout.setContentsMargins(24, 24, 24, 24)
            layout.setSpacing(12)
            
            close_layout = QHBoxLayout()
            close_layout.addStretch(1)
            close_button = QPushButton("✕")
            close_button.setCursor(Qt.PointingHandCursor)
            close_button.setFixedSize(36, 36)
            close_button.clicked.connect(self.close)
            close_button.setStyleSheet("""
                  QPushButton {
                        color: #E8EAED;
                        background-color: rgba(255, 255, 255, 0.08);
                        border: 1px solid rgba(255, 255, 255, 0.15);
                        border-radius: 18px;
                        font-size: 16px;
                        font-weight: bold;
                  }
                  QPushButton:hover {
                        background-color: rgba(255, 255, 255, 0.15);
                        color: white;
                  }
            """)
            close_layout.addWidget(close_button)
            layout.addLayout(close_layout)
            
            self.image_label = QLabel()
            self.image_label.setAlignment(Qt.AlignCenter)
            
            pixmap = QPixmap(image_path)
            desktop = QApplication.desktop()
            screen_geom = desktop.screenGeometry(self)
            max_w = int(screen_geom.width() * 0.85)
            max_h = int(screen_geom.height() * 0.85)
            
            scaled = pixmap.scaled(max_w, max_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.image_label.setPixmap(scaled)
            
            layout.addWidget(self.image_label, 1)
            self.setGeometry(screen_geom)
            self.setFocusPolicy(Qt.StrongFocus)
            
      def mousePressEvent(self, event):
            self.close()
            super().mousePressEvent(event)
            
      def keyPressEvent(self, event):
            if event.key() == Qt.Key_Escape:
                  self.close()
            super().keyPressEvent(event)

class ClickableChatEdit(QTextEdit):
      def __init__(self, parent=None, on_image_click=None):
            super().__init__(parent)
            self.on_image_click = on_image_click

      def mousePressEvent(self, event):
            href = self.anchorAt(event.pos())
            if href:
                  if href.startswith("file://") and (href.endswith(".jpg") or href.endswith(".png") or href.endswith(".jpeg") or href.endswith(".webp")):
                        local_path = href.replace("file:///", "").replace("file://", "")
                        local_path = os.path.normpath(local_path)
                        if os.path.exists(local_path):
                              if self.on_image_click:
                                    self.on_image_click(local_path)
                                    return
                  QDesktopServices.openUrl(QUrl(href))
                  return
            super().mousePressEvent(event)

class ChatSection(QWidget):
      def __init__(self):
            super(ChatSection, self).__init__()
            self.message_html = []
            layout = QVBoxLayout(self)
            layout.setContentsMargins(42, 28, 42, 32)
            layout.setSpacing(16)

            header_layout = QHBoxLayout()
            title_group = QHBoxLayout()
            title_group.setSpacing(14)
            self.voice_orb = QLabel()
            self.voice_orb.setFixedSize(52, 52)
            self.voice_orb.setStyleSheet("""
                  QLabel {
                        border-radius: 26px;
                        background: qradialgradient(
                              cx: 0.34, cy: 0.32, radius: 0.84,
                              fx: 0.30, fy: 0.28,
                              stop: 0 #D2E3FC,
                              stop: 0.34 #8AB4F8,
                              stop: 0.58 #81C995,
                              stop: 0.78 #FDD663,
                              stop: 1 #F28B82
                        );
                  }
            """)
            title_text = QVBoxLayout()
            title_text.setSpacing(2)
            title = QLabel(str(Assistantname).capitalize())
            title.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 22px; font-weight: 600;")
            subtitle = QLabel("Voice and chat in one place")
            subtitle.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
            title_text.addWidget(title)
            title_text.addWidget(subtitle)
            title_group.addWidget(self.voice_orb)
            title_group.addLayout(title_text)

            self.label = QLabel("Available...")
            self.label.setAlignment(Qt.AlignCenter)
            self.label.setMinimumWidth(150)
            self.label.setStyleSheet(f"""
                  QLabel {{
                        color: {TEXT_PRIMARY};
                        background-color: {PANEL_BACKGROUND_2};
                        border: 1px solid {BORDER};
                        border-radius: 8px;
                        padding: 10px 16px;
                        font-size: 13px;
                        font-weight: 600;
                  }}
            """)
            header_layout.addLayout(title_group)
            header_layout.addStretch(1)
            header_layout.addWidget(self.label)
            layout.addLayout(header_layout)

            self.loading_image_blocks = {}
            self.chat_text_edit = ClickableChatEdit(on_image_click=self.openImageLightbox)
            self.chat_text_edit.setReadOnly(True)
            self.chat_text_edit.setTextInteractionFlags(Qt.TextSelectableByMouse)
            self.chat_text_edit.setFrameStyle(QFrame.NoFrame)
            self.chat_text_edit.setFont(QFont("Segoe UI", 11))
            self.chat_text_edit.setStyleSheet(f"""
                  QTextEdit {{
                        background-color: {PANEL_BACKGROUND};
                        color: {TEXT_PRIMARY};
                        border: 1px solid {BORDER};
                        border-radius: 8px;
                        padding: 18px;
                        selection-background-color: {ACCENT};
                        selection-color: #07110F;
                  }}
                  QScrollBar:vertical {{
                        background: {PANEL_BACKGROUND};
                        width: 10px;
                        margin: 8px 0;
                  }}
                  QScrollBar::handle:vertical {{
                        background: #39465A;
                        border-radius: 5px;
                        min-height: 28px;
                  }}
                  QScrollBar::add-line:vertical,
                  QScrollBar::sub-line:vertical {{
                        height: 0;
                  }}
                  QScrollBar::add-page:vertical,
                  QScrollBar::sub-page:vertical {{
                        background: transparent;
                  }}
            """)
            # Create double pane layout
            self.middle_container = QWidget()
            self.middle_container.setStyleSheet("border: none; background: transparent;")
            middle_layout = QHBoxLayout(self.middle_container)
            middle_layout.setContentsMargins(0, 0, 0, 0)
            middle_layout.setSpacing(12)
            
            # Left pane: chat history
            middle_layout.addWidget(self.chat_text_edit, 7)
            
            # Right pane: Dashboard widget
            self.dashboard_widget = QWidget()
            self.dashboard_widget.setMinimumWidth(260)
            self.dashboard_widget.setStyleSheet(f"""
                  QWidget {{
                        background-color: {PANEL_BACKGROUND};
                        border: 1px solid {BORDER};
                        border-radius: 8px;
                  }}
            """)
            dash_layout = QVBoxLayout(self.dashboard_widget)
            dash_layout.setContentsMargins(10, 10, 10, 10)
            dash_layout.setSpacing(10)
            
            # 1. Weather Card
            self.weather_card = QFrame()
            self.weather_card.setStyleSheet(f"background-color: {PANEL_BACKGROUND_2}; border-radius: 6px; border: 1px solid {BORDER};")
            w_layout = QVBoxLayout(self.weather_card)
            w_layout.setContentsMargins(10, 10, 10, 10)
            w_layout.setSpacing(4)
            
            w_header = QLabel("WEATHER FORECAST")
            w_header.setStyleSheet(f"color: {ACCENT}; font-size: 10px; font-weight: 700; border: none; background: transparent;")
            self.weather_city_label = QLabel("Location: Detecting...")
            self.weather_city_label.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 13px; font-weight: 600; border: none; background: transparent;")
            self.weather_temp_label = QLabel("--°C")
            self.weather_temp_label.setStyleSheet(f"color: {ACCENT_2}; font-size: 20px; font-weight: 700; border: none; background: transparent;")
            self.weather_desc_label = QLabel("Awaiting weather status...")
            self.weather_desc_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px; border: none; background: transparent;")
            
            w_layout.addWidget(w_header)
            w_layout.addWidget(self.weather_city_label)
            w_layout.addWidget(self.weather_temp_label)
            w_layout.addWidget(self.weather_desc_label)
            dash_layout.addWidget(self.weather_card)
            
            # 2. Smart Home Card
            self.sh_card = QFrame()
            self.sh_card.setStyleSheet(f"background-color: {PANEL_BACKGROUND_2}; border-radius: 6px; border: 1px solid {BORDER};")
            sh_layout = QVBoxLayout(self.sh_card)
            sh_layout.setContentsMargins(10, 10, 10, 10)
            sh_layout.setSpacing(6)
            
            sh_header = QLabel("SMART HOME SIMULATOR")
            sh_header.setStyleSheet(f"color: {ACCENT}; font-size: 10px; font-weight: 700; border: none; background: transparent;")
            sh_layout.addWidget(sh_header)
            
            # Smart Home buttons grid
            self.sh_grid = QWidget()
            self.sh_grid.setStyleSheet("border: none; background: transparent;")
            sh_grid_layout = QGridLayout(self.sh_grid)
            sh_grid_layout.setContentsMargins(0, 0, 0, 0)
            sh_grid_layout.setSpacing(6)
            
            # Button Styles
            self.btn_lr_light = QPushButton("Light: OFF")
            self.btn_lr_light.setCursor(Qt.PointingHandCursor)
            self.btn_lr_light.clicked.connect(lambda: self.toggleSmartHomeDevice("living_room_light"))
            
            self.btn_bd_ac = QPushButton("AC: OFF")
            self.btn_bd_ac.setCursor(Qt.PointingHandCursor)
            self.btn_bd_ac.clicked.connect(lambda: self.toggleSmartHomeDevice("bedroom_ac"))
            
            self.btn_kt_bulb = QPushButton("Bulb: OFF")
            self.btn_kt_bulb.setCursor(Qt.PointingHandCursor)
            self.btn_kt_bulb.clicked.connect(lambda: self.toggleSmartHomeDevice("kitchen_bulb"))
            
            self.btn_tv = QPushButton("TV: OFF")
            self.btn_tv.setCursor(Qt.PointingHandCursor)
            self.btn_tv.clicked.connect(lambda: self.toggleSmartHomeDevice("smart_tv"))
            
            # Style each button initial state
            btn_style = f"""
                  QPushButton {{
                        color: {TEXT_PRIMARY};
                        background-color: {PANEL_BACKGROUND};
                        border: 1px solid {BORDER};
                        border-radius: 4px;
                        padding: 6px 4px;
                        font-size: 11px;
                        font-weight: 600;
                  }}
            """
            self.btn_lr_light.setStyleSheet(btn_style)
            self.btn_bd_ac.setStyleSheet(btn_style)
            self.btn_kt_bulb.setStyleSheet(btn_style)
            self.btn_tv.setStyleSheet(btn_style)
            
            sh_grid_layout.addWidget(self.btn_lr_light, 0, 0)
            sh_grid_layout.addWidget(self.btn_bd_ac, 0, 1)
            sh_grid_layout.addWidget(self.btn_kt_bulb, 1, 0)
            sh_grid_layout.addWidget(self.btn_tv, 1, 1)
            
            sh_layout.addWidget(self.sh_grid)
            dash_layout.addWidget(self.sh_card)
            
            # 3. Reminders Card
            self.rem_card = QFrame()
            self.rem_card.setStyleSheet(f"background-color: {PANEL_BACKGROUND_2}; border-radius: 6px; border: 1px solid {BORDER};")
            rem_layout = QVBoxLayout(self.rem_card)
            rem_layout.setContentsMargins(10, 10, 10, 10)
            rem_layout.setSpacing(6)
            
            rem_header = QLabel("ACTIVE REMINDERS")
            rem_header.setStyleSheet(f"color: {ACCENT}; font-size: 10px; font-weight: 700; border: none; background: transparent;")
            self.reminders_display = QLabel("No active reminders.")
            self.reminders_display.setWordWrap(True)
            self.reminders_display.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 11px; border: none; background: transparent;")
            
            rem_layout.addWidget(rem_header)
            rem_layout.addWidget(self.reminders_display)
            dash_layout.addWidget(self.rem_card)
            
            dash_layout.addStretch(1)
            middle_layout.addWidget(self.dashboard_widget, 3)
            
            layout.addWidget(self.middle_container, 1)

            self.pending_attachments = []
            self.attachments_container = QWidget()
            self.attachments_container.setVisible(False)
            self.attachments_layout = QHBoxLayout(self.attachments_container)
            self.attachments_layout.setContentsMargins(0, 0, 0, 0)
            self.attachments_layout.setSpacing(8)
            self.attachments_layout.addStretch(1)
            layout.addWidget(self.attachments_container)

            bottom_layout = QHBoxLayout()
            bottom_layout.setSpacing(12)

            self.input_box = PasteAwareLineEdit(self.handlePastedImage)
            self.input_box.setPlaceholderText("Type a message...")
            self.input_box.returnPressed.connect(self.submitTypedMessage)
            self.input_box.setStyleSheet(f"""
                  QLineEdit {{
                        color: {TEXT_PRIMARY};
                        background-color: {PANEL_BACKGROUND};
                        border: 1px solid {BORDER};
                        border-radius: 22px;
                        padding: 12px 16px;
                        font-size: 14px;
                  }}
                  QLineEdit:focus {{
                        border: 1px solid {ACCENT};
                  }}
            """)

            send_button = QPushButton("Send")
            send_button.setCursor(Qt.PointingHandCursor)
            send_button.clicked.connect(self.submitTypedMessage)
            send_button.setFixedHeight(46)
            send_button.setStyleSheet(f"""
                  QPushButton {{
                        color: #202124;
                        background-color: {ACCENT};
                        border: none;
                        border-radius: 23px;
                        padding: 0 20px;
                        font-size: 14px;
                        font-weight: 600;
                  }}
                  QPushButton:hover {{
                        background-color: #AECBFA;
                  }}
            """)

            upload_button = QPushButton("Attach")
            upload_button.setCursor(Qt.PointingHandCursor)
            upload_button.clicked.connect(self.uploadFiles)
            upload_button.setFixedHeight(46)
            upload_button.setStyleSheet(f"""
                  QPushButton {{
                        color: {TEXT_PRIMARY};
                        background-color: {PANEL_BACKGROUND_2};
                        border: 1px solid {BORDER};
                        border-radius: 23px;
                        padding: 0 18px;
                        font-size: 14px;
                        font-weight: 600;
                  }}
                  QPushButton:hover {{
                        border-color: {ACCENT};
                        background-color: #2A2B2F;
                  }}
            """)

            self.mic_button = QPushButton("Mic on")
            self.mic_button.setCursor(Qt.PointingHandCursor)
            self.mic_button.clicked.connect(self.toggleMic)
            self.mic_active = True

            listen_button = QPushButton("Listen")
            listen_button.setCursor(Qt.PointingHandCursor)
            listen_button.clicked.connect(self.listenNow)
            listen_button.setFixedHeight(46)
            listen_button.setStyleSheet(f"""
                  QPushButton {{
                        color: {TEXT_PRIMARY};
                        background-color: {PANEL_BACKGROUND_2};
                        border: 1px solid {BORDER};
                        border-radius: 23px;
                        padding: 0 18px;
                        font-size: 14px;
                        font-weight: 600;
                  }}
                  QPushButton:hover {{
                        border-color: {ACCENT};
                        background-color: #2A2B2F;
                  }}
            """)

            stop_button = QPushButton("End")
            stop_button.setCursor(Qt.PointingHandCursor)
            stop_button.clicked.connect(self.endCurrentResponse)
            stop_button.setFixedHeight(46)
            stop_button.setStyleSheet("""
                  QPushButton {
                        color: white;
                        background-color: #D93025;
                        border: none;
                        border-radius: 23px;
                        padding: 0 18px;
                        font-size: 14px;
                        font-weight: 600;
                  }
                  QPushButton:hover {
                        background-color: #EA4335;
                  }
            """)

            bottom_layout.addWidget(self.input_box, 1)
            bottom_layout.addWidget(upload_button)
            bottom_layout.addWidget(send_button)
            bottom_layout.addWidget(self.mic_button)
            bottom_layout.addWidget(listen_button)
            bottom_layout.addWidget(stop_button)
            layout.addLayout(bottom_layout)
            self.renderMicButton()
            self.setStyleSheet(f"background-color: {APP_BACKGROUND};")

            self.timer = QTimer(self)
            self.timer.timeout.connect(self.loadMessages)
            self.timer.timeout.connect(self.loadGeneratedImages)
            self.timer.timeout.connect(self.SpeechRecogText)
            self.timer.timeout.connect(self.updateDashboard)
            self.timer.start(100)

      def openImageLightbox(self, image_path):
            lightbox = ImageLightbox(image_path, self)
            lightbox.exec_()

      def submitTypedMessage(self):
            global old_chat_message
            text = self.input_box.text().strip()
            if not text:
                  return

            RequestStopSpeaking()
            attached_names = [item.get("name", "attachment") for item in self.pending_attachments]
            message_text = text
            if attached_names:
                  message_text = (
                        f"{text}\n\n"
                        f"Use these attached file(s) as context for this request: {', '.join(attached_names)}"
                  )

            SendTypedMessage(message_text)
            local_message = f"{Username} : {text}"
            self.addMessage(local_message)
            old_chat_message = local_message
            
            # Clear Response.data to prevent previous assistant answer duplication
            try:
                with open(TempDirectoryPath("Response.data"), "w", encoding="utf-8") as file:
                    file.write("")
            except Exception:
                pass
                
            self.input_box.clear()
            self.pending_attachments = []
            self.refreshAttachments()

      def uploadFiles(self):
            added = UploadFiles(self)
            if not added:
                  return

            self.pending_attachments.extend(added)
            self.refreshAttachments()
            SetAssistantStatus("File attached")

      def handlePastedImage(self, added):
            if not added:
                  return

            self.pending_attachments.extend(added)
            self.refreshAttachments()
            SetAssistantStatus("Image pasted")

      def refreshAttachments(self):
            while self.attachments_layout.count():
                  item = self.attachments_layout.takeAt(0)
                  widget = item.widget()
                  if widget:
                        widget.deleteLater()

            if not self.pending_attachments:
                  self.attachments_container.setVisible(False)
                  self.attachments_layout.addStretch(1)
                  return

            self.attachments_container.setVisible(True)

            for item in self.pending_attachments:
                  self.attachments_layout.addWidget(self.createAttachmentPreview(item))

            self.attachments_layout.addStretch(1)

      def createAttachmentPreview(self, item):
            ext = str(item.get("ext", "")).lower()
            path = item.get("path", "")

            if ext in [".png", ".jpg", ".jpeg", ".webp"] and os.path.exists(path):
                  wrapper = QWidget()
                  wrapper.setFixedSize(64, 64)
                  wrapper.setStyleSheet("background: transparent; border: none;")
                  
                  preview = QLabel(wrapper)
                  preview.setFixedSize(64, 64)
                  
                  pix = QPixmap(path)
                  scaled_pix = pix.scaled(64, 64, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                  
                  cropped = QPixmap(64, 64)
                  cropped.fill(Qt.transparent)
                  painter = QPainter(cropped)
                  x_offset = (scaled_pix.width() - 64) // 2
                  y_offset = (scaled_pix.height() - 64) // 2
                  painter.drawPixmap(0, 0, scaled_pix, x_offset, y_offset, 64, 64)
                  painter.end()
                  
                  preview.setPixmap(cropped)
                  preview.setStyleSheet(f"border-radius: 8px; border: 1px solid {BORDER};")
                  
                  remove_button = QPushButton("×", wrapper)
                  remove_button.setCursor(Qt.PointingHandCursor)
                  remove_button.setFixedSize(18, 18)
                  remove_button.move(44, 2)
                  remove_button.clicked.connect(lambda _, current=item: self.removeAttachment(current))
                  remove_button.setStyleSheet("""
                        QPushButton {
                              color: white;
                              background-color: rgba(10, 10, 12, 0.7);
                              border: 1px solid rgba(255, 255, 255, 0.25);
                              border-radius: 9px;
                              font-size: 11px;
                              font-weight: bold;
                        }
                        QPushButton:hover {
                              background-color: rgba(217, 48, 37, 0.95);
                              border-color: transparent;
                        }
                  """)
                  return wrapper

            wrapper = QWidget()
            wrapper.setStyleSheet(f"""
                  QWidget {{
                        background-color: {PANEL_BACKGROUND_2};
                        border: 1px solid {BORDER};
                        border-radius: 8px;
                  }}
            """)
            row = QHBoxLayout(wrapper)
            row.setContentsMargins(8, 6, 6, 6)
            row.setSpacing(8)

            name_label = QLabel(item.get("name", "attachment"))
            name_label.setMaximumWidth(210)
            name_label.setStyleSheet(f"color: {TEXT_PRIMARY}; border: none; font-size: 12px;")
            row.addWidget(name_label)

            remove_button = QPushButton("X")
            remove_button.setCursor(Qt.PointingHandCursor)
            remove_button.setFixedSize(24, 24)
            remove_button.clicked.connect(lambda _, current=item: self.removeAttachment(current))
            remove_button.setStyleSheet("""
                  QPushButton {
                        color: white;
                        background-color: #D93025;
                        border: none;
                        border-radius: 12px;
                        font-size: 11px;
                        font-weight: 700;
                  }
                  QPushButton:hover {
                        background-color: #EA4335;
                  }
            """)
            row.addWidget(remove_button)
            return wrapper

      def removeAttachment(self, item):
            remove_upload(item.get("path", ""))
            self.pending_attachments = [
                  existing for existing in self.pending_attachments
                  if existing.get("path") != item.get("path")
            ]
            self.refreshAttachments()
            SetAssistantStatus("Attachment removed")

      def toggleMic(self):
            if self.mic_active:
                  self.listenNow()
                  return

            self.mic_active = True
            MicButtonClosed()
            RequestDirectListen()
            self.renderMicButton()

      def renderMicButton(self):
            text = "Mic" if self.mic_active else "Muted"
            bg = "#E8EAED" if self.mic_active else "#303134"
            fg = "#202124" if self.mic_active else TEXT_MUTED
            border = "transparent" if self.mic_active else "#5F6368"
            self.mic_button.setText(text)
            self.mic_button.setFixedHeight(46)
            self.mic_button.setStyleSheet(f"""
                  QPushButton {{
                        color: {fg};
                        background-color: {bg};
                        border: 1px solid {border};
                        border-radius: 23px;
                        padding: 0 18px;
                        font-size: 14px;
                        font-weight: 600;
                  }}
                  QPushButton:hover {{
                        background-color: #F1F3F4;
                        color: #202124;
                  }}
            """)

      def endCurrentResponse(self):
            RequestStopSpeaking()
            MicButtonInitiated()
            self.mic_active = False
            self.renderMicButton()

      def listenNow(self):
            MicButtonClosed()
            self.mic_active = True
            self.renderMicButton()
            RequestDirectListen()

      def loadMessages(self):
            global old_chat_message

            messages = _read_temp_file('Response.data')

            if not messages or len(messages) <= 1 or str(old_chat_message) == str(messages):
                  return

            self.addMessage(message=messages)
            old_chat_message = messages

      def loadGeneratedImages(self):
            event = _read_and_clear_temp_file("ImageResult.data")
            if not event:
                  return

            parts = event.split("|", 2)
            if len(parts) < 2:
                  return

            status = parts[0]
            prompt = parts[1]
            payload = parts[2] if len(parts) > 2 else ""

            if status == "loading":
                  self.addImageLoading(prompt)
            elif status == "done":
                  paths = [path for path in payload.split(";") if path and os.path.exists(path)]
                  if paths:
                        self.addGeneratedImages(prompt, paths)
            elif status == "error":
                  escaped_prompt = prompt.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                  error_html = f"""
                        <div style="
                              margin: 14px 0;
                              padding: 14px 16px;
                              background-color: {PANEL_BACKGROUND_2};
                              border-left: 3px solid #F46D75;
                              border-radius: 6px;
                        ">
                              <div style="color: #F46D75; font-size: 9pt; font-weight: 600; margin-bottom: 8px;">{Assistantname}</div>
                              <div style="color: {TEXT_PRIMARY}; font-size: 11pt;">I could not generate that image right now.</div>
                              <div style="color: {TEXT_MUTED}; font-size: 9pt; margin-top: 8px;">{escaped_prompt}</div>
                        </div>
                  """
                  if prompt in self.loading_image_blocks:
                        idx = self.loading_image_blocks[prompt]
                        if idx < len(self.message_html):
                              self.message_html[idx] = error_html
                              del self.loading_image_blocks[prompt]
                        else:
                              self.message_html.append(error_html)
                  else:
                        self.message_html.append(error_html)
                  self.renderChatHtml()

      def SpeechRecogText(self):
            message = _read_temp_file('Status.data', "Available...")
            self.label.setText(message)

            if "Listening" in message:
                  color = ACCENT
            elif "Thinking" in message or "Searching" in message or "Generating" in message:
                  color = ACCENT_2
            elif "failed" in message.lower() or "error" in message.lower():
                  color = "#F46D75"
            else:
                  color = TEXT_MUTED

            self.label.setStyleSheet(f"""
                  QLabel {{
                        color: {TEXT_PRIMARY};
                        background-color: {PANEL_BACKGROUND_2};
                        border: 1px solid {color};
                        border-radius: 8px;
                        padding: 10px 16px;
                        font-size: 13px;
                        font-weight: 600;
                  }}
            """)

      def toggleSmartHomeDevice(self, device_key):
            import json
            state_file = os.path.join("Data", "smart_home.json")
            try:
                  with open(state_file, "r", encoding="utf-8") as f:
                        devices = json.load(f)
            except Exception:
                  return

            if device_key in devices:
                  dev = devices[device_key]
                  if dev["state"] == "on":
                        dev["state"] = "off"
                  else:
                        dev["state"] = "on"

                  with open(state_file, "w", encoding="utf-8") as f:
                        json.dump(devices, f, indent=4)

                  self.updateDashboard()

      def updateDashboard(self):
            import json
            import time
            import datetime

            # Update Weather
            weather_file = os.path.join("Data", "weather_state.json")
            if os.path.exists(weather_file):
                  try:
                        with open(weather_file, "r", encoding="utf-8") as f:
                              w = json.load(f)
                        self.weather_city_label.setText(w.get("city", "Detecting..."))
                        self.weather_temp_label.setText(w.get("temp", "--°C"))
                        self.weather_desc_label.setText(w.get("desc", ""))
                  except Exception:
                        pass

            # Update Smart Home
            sh_file = os.path.join("Data", "smart_home.json")
            if os.path.exists(sh_file):
                  try:
                        with open(sh_file, "r", encoding="utf-8") as f:
                              devices = json.load(f)
                        
                        def style_btn(btn, key, dev):
                              name = dev["name"].replace(" Room", "").replace(" Light", "").replace(" Bulb", "")
                              state = dev["state"].upper()
                              if key == "bedroom_ac" and state == "ON":
                                    btn.setText(f"{name}: {dev.get('temperature', 24)}°C")
                              else:
                                    btn.setText(f"{name}: {state}")
                              
                              if state == "ON":
                                    btn.setStyleSheet(f"""
                                          QPushButton {{
                                                color: #202124;
                                                background-color: {ACCENT};
                                                border: 1px solid {ACCENT};
                                                border-radius: 4px;
                                                padding: 6px 4px;
                                                font-size: 11px;
                                                font-weight: 700;
                                          }}
                                    """)
                              else:
                                    btn.setStyleSheet(f"""
                                          QPushButton {{
                                                color: {TEXT_PRIMARY};
                                                background-color: {PANEL_BACKGROUND};
                                                border: 1px solid {BORDER};
                                                border-radius: 4px;
                                                padding: 6px 4px;
                                                font-size: 11px;
                                                font-weight: 600;
                                          }}
                                    """)
                        
                        style_btn(self.btn_lr_light, "living_room_light", devices["living_room_light"])
                        style_btn(self.btn_bd_ac, "bedroom_ac", devices["bedroom_ac"])
                        style_btn(self.btn_kt_bulb, "kitchen_bulb", devices["kitchen_bulb"])
                        style_btn(self.btn_tv, "smart_tv", devices["smart_tv"])
                  except Exception as e:
                        print(f"Failed to load smart home in GUI: {e}")

            # Update Reminders
            rem_file = os.path.join("Data", "reminders.json")
            if os.path.exists(rem_file):
                  try:
                        with open(rem_file, "r", encoding="utf-8") as f:
                              reminders = json.load(f)
                        
                        active = [r for r in reminders if not r.get("notified")]
                        if active:
                              text_list = []
                              for r in active[:4]: # Show top 4
                                    t = r.get("time", 0)
                                    time_str = datetime.datetime.fromtimestamp(t).strftime("%I:%M %p")
                                    text_list.append(f"• {r.get('message')} ({time_str})")
                              self.reminders_display.setText("\n".join(text_list))
                        else:
                              self.reminders_display.setText("No active reminders.")
                  except Exception:
                        pass

      def addMessage(self, message):
            blocks = []
            for line in message.splitlines():
                  line = line.strip()
                  if not line:
                        continue

                  escaped = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                  speaker = Assistantname
                  content = escaped
                  if " : " in escaped:
                        speaker, content = escaped.split(" : ", 1)

                  is_user = speaker.lower().startswith("user") or speaker.lower().startswith(Username.lower().split()[0])
                  accent = ACCENT if is_user else "#C58AF9"
                  speaker_label = "You" if is_user else Assistantname

                  blocks.append(f"""
                        <div style="
                              margin: 14px 0;
                              padding: 14px 16px;
                              background-color: {PANEL_BACKGROUND_2};
                              border-left: 3px solid {accent};
                              border-radius: 6px;
                        ">
                              <div style="
                                    color: {accent};
                                    font-size: 9pt;
                                    font-weight: 600;
                                    margin-bottom: 6px;
                              ">{speaker_label}</div>
                              <div style="
                                    color: {TEXT_PRIMARY};
                                    font-size: 11pt;
                                    line-height: 1.48;
                              ">{content}</div>
                        </div>
                  """)

            if not blocks:
                  return

            self.message_html.extend(blocks)
            self.chat_text_edit.setHtml(f"""
                  <html>
                        <body style="font-family: Segoe UI; font-size: 11pt; background-color: {PANEL_BACKGROUND};">
                              {''.join(self.message_html)}
                        </body>
                  </html>
            """)
            self.chat_text_edit.moveCursor(QTextCursor.End)

      def addImageLoading(self, prompt):
            escaped_prompt = prompt.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            src = _image_src(GraphicsDirectoryPath("buffering.gif"))
            
            loading_html = f"""
                  <div style="
                        margin: 14px 0;
                        padding: 14px 16px;
                        background-color: {PANEL_BACKGROUND_2};
                        border-left: 3px solid {ACCENT_2};
                        border-radius: 6px;
                  ">
                        <div style="color: {ACCENT_2}; font-size: 9pt; font-weight: 600; margin-bottom: 8px;">{Assistantname}</div>
                        <div>
                              <img src="{src}" width="260" height="180" style="border-radius: 8px; border: 1px solid #34363A;" />
                        </div>
                        <div style="color: {TEXT_MUTED}; font-size: 9pt; margin-top: 8px;">Generating: {escaped_prompt}</div>
                  </div>
            """
            self.loading_image_blocks[prompt] = len(self.message_html)
            self.message_html.append(loading_html)
            self.renderChatHtml()

      def addGeneratedImages(self, prompt, paths):
            escaped_prompt = prompt.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            image_blocks = []

            for path in paths:
                  src = _image_src(path)
                  image_blocks.append(f"""
                        <a href="{src}">
                              <img src="{src}" width="260" style="border-radius: 8px; border: 1px solid #34363A;" />
                        </a>
                  """)

            done_html = f"""
                  <div style="
                        margin: 14px 0;
                        padding: 14px 16px;
                        background-color: {PANEL_BACKGROUND_2};
                        border-left: 3px solid #81C995;
                        border-radius: 6px;
                  ">
                        <div style="color: #81C995; font-size: 9pt; font-weight: 600; margin-bottom: 8px;">{Assistantname}</div>
                        {''.join(image_blocks)}
                        <div style="color: {TEXT_MUTED}; font-size: 9pt; margin-top: 8px;">{escaped_prompt}</div>
                  </div>
            """
            
            if prompt in self.loading_image_blocks:
                  idx = self.loading_image_blocks[prompt]
                  if idx < len(self.message_html):
                        self.message_html[idx] = done_html
                        del self.loading_image_blocks[prompt]
                  else:
                        self.message_html.append(done_html)
            else:
                  self.message_html.append(done_html)
                  
            self.renderChatHtml()

      def renderChatHtml(self):
            self.chat_text_edit.setHtml(f"""
                  <html>
                        <body style="font-family: Segoe UI; font-size: 11pt; background-color: {PANEL_BACKGROUND};">
                              {''.join(self.message_html)}
                        </body>
                  </html>
            """)
            self.chat_text_edit.moveCursor(QTextCursor.End)


# class InitialScreen(QWidget):
# 
#       def __init__(self, parent=None):
#             super().__init__(parent)
#             desktop = QApplication.desktop()
#             screen_width = desktop.screenGeometry().width()
#             screen_height = desktop.screenGeometry().height()
# 
#             content_layout = QVBoxLayout()
#             content_layout.setContentsMargins(72, 54, 72, 58)
#             content_layout.setSpacing(18)
# 
#             content_layout.addStretch(1)
# 
#             brand_label = QLabel(str(Assistantname).upper())
#             brand_label.setAlignment(Qt.AlignCenter)
#             brand_label.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 30px; font-weight: 600; letter-spacing: 0;")
#             content_layout.addWidget(brand_label)
# 
#             subtitle = QLabel("Voice chat")
#             subtitle.setAlignment(Qt.AlignCenter)
#             subtitle.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 14px;")
#             content_layout.addWidget(subtitle)
# 
#             self.voice_orb = QLabel()
#             self.voice_orb.setFixedSize(214, 214)
#             self.voice_orb.setAlignment(Qt.AlignCenter)
#             self.voice_orb.setStyleSheet("""
#                   QLabel {
#                         border-radius: 107px;
#                         background: qradialgradient(
#                               cx: 0.34, cy: 0.32, radius: 0.84,
#                               fx: 0.30, fy: 0.28,
#                               stop: 0 #D2E3FC,
#                               stop: 0.34 #8AB4F8,
#                               stop: 0.58 #81C995,
#                               stop: 0.78 #FDD663,
#                               stop: 1 #F28B82
#                         );
#                   }
#             """)
#             glow = QGraphicsDropShadowEffect(self.voice_orb)
#             glow.setBlurRadius(48)
#             glow.setOffset(0, 0)
#             glow.setColor(QColor(138, 180, 248, 120))
#             self.voice_orb.setGraphicsEffect(glow)
#             content_layout.addWidget(self.voice_orb, alignment=Qt.AlignCenter)
# 
#             self.label = QLabel("Available...")
#             self.label.setAlignment(Qt.AlignCenter)
#             self.label.setStyleSheet(f"""
#                   QLabel {{
#                         color: {TEXT_MUTED};
#                         background-color: transparent;
#                         border: none;
#                         padding: 8px 18px;
#                         font-size: 16px;
#                         font-weight: 500;
#                   }}
#             """)
#             content_layout.addWidget(self.label, alignment=Qt.AlignCenter)
# 
#             controls = QHBoxLayout()
#             controls.setSpacing(18)
#             controls.setAlignment(Qt.AlignCenter)
# 
#             self.icon_label = QLabel()
#             self.icon_label.setFixedSize(72, 72)
#             self.icon_label.setAlignment(Qt.AlignCenter)
#             self.listening_active = True
#             self.render_mic_state()
#             self.icon_label.mousePressEvent = self.toggle_icon
# 
#             end_button = QPushButton("End")
#             end_button.setCursor(Qt.PointingHandCursor)
#             end_button.setFixedSize(72, 72)
#             end_button.clicked.connect(RequestStopSpeaking)
#             end_button.setStyleSheet("""
#                   QPushButton {
#                         color: white;
#                         background-color: #D93025;
#                         border: none;
#                         border-radius: 36px;
#                         font-size: 14px;
#                         font-weight: 600;
#                   }
#                   QPushButton:hover {
#                         background-color: #EA4335;
#                   }
#             """)
# 
#             controls.addWidget(self.icon_label)
#             controls.addWidget(end_button)
#             content_layout.addLayout(controls)
# 
#             content_layout.addStretch(1)
#             self.setLayout(content_layout)
#             self.setMinimumSize(760, 520)
#             self.setStyleSheet(f"background-color: {APP_BACKGROUND};")
#             self.timer = QTimer(self)
#             self.timer.timeout.connect(self.SpeechRecogText)
#             self.timer.start(100)
# 
#       def SpeechRecogText(self):
#             messages = _read_temp_file('Status.data', "Available...")
#             self.label.setText(messages)
# 
#       def load_icon(self, path, width=52, height=52):
#             pixmap = QPixmap(path)
#             new_pixmap = pixmap.scaled(width, height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
#             self.icon_label.setPixmap(new_pixmap)
# 
#       def render_mic_state(self):
#             if self.listening_active:
#                   self.load_icon(GraphicsDirectoryPath('Mic_on.svg'), 34, 34)
#                   self.icon_label.setStyleSheet(f"""
#                         QLabel {{
#                               background-color: #E8EAED;
#                               border: none;
#                               border-radius: 36px;
#                               padding: 19px;
#                         }}
#                   """)
#                   MicButtonClosed()
# 
#             else:
#                   self.load_icon(GraphicsDirectoryPath('Mic_off.svg'), 34, 34)
#                   self.icon_label.setStyleSheet(f"""
#                         QLabel {{
#                               background-color: #303134;
#                               border: 1px solid #5F6368;
#                               border-radius: 36px;
#                               padding: 19px;
#                         }}
#                   """)
#                   MicButtonInitiated()
# 
#       def toggle_icon(self, event=None):
#             self.listening_active = not self.listening_active
#             self.render_mic_state()


class MessageScreen(QWidget):

      def __init__(self, parent = None):
            super().__init__(parent)
            desktop = QApplication.desktop()
            screen_width = desktop.screenGeometry().width()
            screen_height = desktop.screenGeometry().height()
            layout = QVBoxLayout()
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
            chat_section = ChatSection()
            layout.addWidget(chat_section)
            self.setLayout(layout)
            self.setStyleSheet(f"background-color: {APP_BACKGROUND};")
            self.setMinimumSize(760, 520)

class CustomTopBar(QWidget):

      def __init__(self, parent, stacked_widget):
            super().__init__(parent)
            self.initUI()
            self.current_screen = None
            self.stacked_widget = stacked_widget

      def initUI(self):
            self.setFixedHeight(56)
            layout = QHBoxLayout(self)
            layout.setContentsMargins(18, 8, 18, 8)
            layout.setSpacing(8)
            layout.setAlignment(Qt.AlignVCenter)
#             nav_style = f"""
#                   QPushButton {{
#                         height: 34px;
#                         padding: 0 13px;
#                         border-radius: 17px;
#                         background-color: transparent;
#                         color: {TEXT_PRIMARY};
#                         border: 1px solid transparent;
#                         font-size: 13px;
#                         font-weight: 500;
#                   }}
#                   QPushButton:hover {{
#                         background-color: #2A2B2F;
#                   }}
#             """
            minimize_button = QPushButton()
            minimize_button.setText("-")
            window_button_style = f"""
                  QPushButton {{
                        color: {TEXT_PRIMARY};
                        min-width: 40px;
                        max-width: 40px;
                        min-height: 34px;
                        max-height: 34px;
                        border-radius: 17px;
                        background-color: transparent;
                        border: 1px solid transparent;
                        font-size: 18px;
                        font-weight: 500;
                  }}
                  QPushButton:hover {{
                        background-color: #2A2B2F;
                  }}
            """
            minimize_button.setCursor(Qt.PointingHandCursor)
            minimize_button.setStyleSheet(window_button_style)
            minimize_button.clicked.connect(self.minimizeWindow)
            self.maximize_button = QPushButton()
            self.maximize_icon = "[]"
            self.restore_icon = "[ ]"
            self.maximize_button.setText(self.maximize_icon)
            self.maximize_button.setFlat(True)
            self.maximize_button.setCursor(Qt.PointingHandCursor)
            self.maximize_button.setStyleSheet(window_button_style)
            self.maximize_button.clicked.connect(self.maximizeWindow)
            close_button = QPushButton()
            close_button.setText("X")
            close_button.setCursor(Qt.PointingHandCursor)
            close_button.setStyleSheet(f"""
                  QPushButton {{
                        color: {TEXT_PRIMARY};
                        min-width: 40px;
                        max-width: 40px;
                        min-height: 34px;
                        max-height: 34px;
                        border-radius: 17px;
                        background-color: transparent;
                        border: 1px solid transparent;
                        font-size: 20px;
                        font-weight: 500;
                  }}
                  QPushButton:hover {{
                        background-color: #C5221F;
                        color: white;
                  }}
            """)
            close_button.clicked.connect(self.closeWindow)
            title_label = QLabel(str(Assistantname).capitalize())
            title_label.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 15px; font-weight: 600;")
            layout.addWidget(title_label)
            layout.addSpacing(14)
            layout.addStretch(1)
            layout.addWidget(minimize_button)
            layout.addWidget(self.maximize_button)
            layout.addWidget(close_button)
            self.draggable = True
            self.offset = None

      def paintEvent(self, event):
            painter = QPainter(self)
            painter.fillRect(self.rect(), QColor(APP_BACKGROUND))
            super().paintEvent(event)

      def minimizeWindow(self):
            self.parent().showMinimized()

      def maximizeWindow(self):
            if self.parent().isMaximized():
                  self.parent().showNormal()
                  self.maximize_button.setText(self.maximize_icon)
            else:
                  self.parent().showMaximized()
                  self.maximize_button.setText(self.restore_icon)


      def closeWindow(self):
            self.parent().close()

      def mousePressEvent(self, event):
            if self.draggable:
                  self.offset = event.pos()
      
      def mouseMoveEvent(self, event):
            if self.draggable and self.offset:
                  new_pos = event.globalPos() - self.offset
                  self.parent().move(new_pos)

#       def showMessageScreen(self):
#             if self.current_screen is not None:
#                   self.current_screen.hide()
# 
#             message_screen = MessageScreen(self)
#             layout = self.parent().layout()
#             if layout is not None:
#                   layout.addWidget(message_screen)
#             self.current_screen = message_screen
# 
#       def showInitialScreen(self):
#             if self.current_screen is not None:
#                   self.current_screen.hide()
# 
#             initial_screen = InitialScreen(self)
#             layout = self.parent().layout()
#             if layout is not None:
#                   layout.addWidget(initial_screen)
#             self.current_screen = initial_screen

class MainWindow(QMainWindow):

      def __init__(self):
            super().__init__()
            self.setWindowFlags(Qt.FramelessWindowHint)
            self.initUI()

      def initUI(self):
            desktop = QApplication.desktop()
            screen_width = desktop.screenGeometry().width()
            screen_height = desktop.screenGeometry().height()
            stacked_widget = QStackedWidget(self)
            message_screen = MessageScreen()
            stacked_widget.addWidget(message_screen)
            width = min(1280, max(900, screen_width - 80))
            height = min(860, max(640, screen_height - 80))
            x = max(0, int((screen_width - width) / 2))
            y = max(0, int((screen_height - height) / 2))
            self.setGeometry(x, y, width, height)
            self.setMinimumSize(900, 640)
            self.setStyleSheet(f"background-color: {APP_BACKGROUND};")
            top_bar = CustomTopBar(self, stacked_widget)
            self.setMenuWidget(top_bar)
            self.setCentralWidget(stacked_widget)

def GraphicalUserInterface():
      app = QApplication(sys.argv)
      window = MainWindow()
      window.show()
      sys.exit(app.exec_())

if __name__ == "__main__":
      GraphicalUserInterface()
