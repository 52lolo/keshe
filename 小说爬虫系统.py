import sys
from PyQt5.Qt import *
import mysql.connector
import request
from lxml import etree

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.43"
}

class NovelSearchWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("小说搜索")
        self.setGeometry(100, 100, 2276, 1280)

        self.setStyleSheet(
            "background-image: url('v2-3b8ec312fedbbd1dc73928c5dce1103b_r.jpg'); background-repeat: no-repeat; background-position: center;")

        self.label = QLabel("请输入小说名称:", self)
        self.label.setGeometry(50, 50, 120, 20)

        self.textbox = QLineEdit(self)
        self.textbox.setGeometry(180, 50, 150, 20)

        self.button = QPushButton("搜索", self)
        self.button.setGeometry(150, 100, 100, 30)
        self.button.clicked.connect(self.search_novel)

        self.chapter_list = QListWidget(self)
        self.chapter_list.setGeometry(50, 150, 300, 200)
        self.chapter_list.itemClicked.connect(self.show_content)

        self.show()

    def search_novel(self):
        novel_name = self.textbox.text()

        create_table_query = '''
        CREATE TABLE IF NOT EXISTS novels (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            chapter_title VARCHAR(100),
            chapter_content TEXT
        )
        '''

        if novel_name:
            # 连接到 MySQL 数据库
            conn = mysql.connector.connect(
                host='localhost',
                user='root',
                password='qq8112105qq',
                database='mydb',
                port='3306',
                use_unicode=True
            )
            print("数据库连接成功")

            cursor = conn.cursor()
            cursor.execute(create_table_query)

            url = "https://www.biquge7.xyz/search"
            data = {
                "keyword": novel_name
            }
            response = requests.get(url=url, params=data, headers=headers)
            root = etree.HTML(response.text)
            xpath = '//div[@class="title"]/a[@title="' + novel_name + '"]/@href'
            t_list = root.xpath(xpath)

            if t_list:
                home_url = "https://www.biquge7.xyz" + t_list[0]
                response = requests.get(url=home_url, headers=headers)
                response.encoding = "utf-8"
                a_xpath = '//div[@class="list"]/ul/li/a'
                base_url = "https://www.biquge7.xyz"
                root = etree.HTML(response.text)
                a_list = root.xpath(a_xpath)
                detail_urls = []
                for a_node in a_list:
                    href = a_node.xpath('./@href')[0]
                    detail_urls.append(base_url + href)

                for detail_url in detail_urls[:5]:
                    response = requests.get(url=detail_url, headers=headers)
                    response.encoding = "utf-8"
                    root = etree.HTML(response.text)
                    title_xpath = '//div/h1/text()'
                    content_xpath = '//div[@class="text"]/text()'
                    title = root.xpath(title_xpath)[0]
                    content_list = root.xpath(content_xpath)
                    content = '\n'.join(content_list)  # 将内容列表拼接为字符串

                    sql = "INSERT INTO novels (name, chapter_title, chapter_content) VALUES (%s, %s, %s)"
                    data = (novel_name, title, content)
                    cursor.execute(sql, data)

            else:
                QMessageBox.warning(self, "错误", "未找到小说")
                self.textbox.clear()  # 清空输入框

            conn.commit()  # 提交事务
            cursor.close()
            conn.close()

            print("关闭数据库")

                # 刷新章节列表
            self.refresh_chapter_list(novel_name)

    def refresh_chapter_list(self, novel_name):
        # 连接到 MySQL 数据库
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='qq8112105qq',
            database='mydb',
            port='3306',
            use_unicode=True
        )
        print("数据库连接成功")

        cursor = conn.cursor()

        # 查询数据库中的章节标题
        sql = "SELECT chapter_title FROM novels WHERE name = %s"
        data = (novel_name,)
        cursor.execute(sql, data)
        chapters = cursor.fetchall()

        # 清空章节列表
        self.chapter_list.clear()

        # 将章节标题添加到列表中
        for chapter in chapters:
            self.chapter_list.addItem(chapter[0])

        cursor.close()
        conn.close()

        print("关闭数据库")
    def show_content(self, item):
        chapter_title = item.text()

        # 连接到 MySQL 数据库
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='qq8112105qq',
            database='mydb',
            port='3306',
            use_unicode=True
        )
        cursor = conn.cursor()

        # 查询数据库中对应章节的内容
        sql = "SELECT chapter_content FROM novels WHERE chapter_title = %s"
        data = (chapter_title,)
        cursor.execute(sql, data)
        result = cursor.fetchone()

        if result:
            content = result[0]

            # 创建自定义对话框并显示章节内容
            content_dialog = QDialog()
            content_dialog.setWindowTitle("章节内容")
            content_dialog.setGeometry(100, 100, 400, 400)

            layout = QVBoxLayout(content_dialog)
            text_edit = QTextEdit(content_dialog)
            text_edit.setPlainText(content)
            text_edit.setReadOnly(True)
            layout.addWidget(text_edit)

            # 创建按钮布局
            button_layout = QHBoxLayout()
            layout.addLayout(button_layout)

            # 上一章节按钮
            prev_button = QPushButton("上一章节", content_dialog)
            prev_button.clicked.connect(lambda: self.show_adjacent_chapter(item, -1))
            button_layout.addWidget(prev_button)

            # 下一章节按钮
            next_button = QPushButton("下一章节", content_dialog)
            next_button.clicked.connect(lambda: self.show_adjacent_chapter(item, 1))
            button_layout.addWidget(next_button)

            # 返回目录按钮
            back_button = QPushButton("返回目录", content_dialog)
            back_button.clicked.connect(content_dialog.close)  # 关闭当前对话框，返回目录
            button_layout.addWidget(back_button)

            content_dialog.exec_()
        else:
            QMessageBox.warning(self, "错误", "未找到章节内容")

        cursor.close()
        conn.close()

    def show_adjacent_chapter(self, item, direction):
        current_row = self.chapter_list.row(item)
        next_row = current_row + direction

        if next_row >= 0 and next_row < self.chapter_list.count():
            next_item = self.chapter_list.item(next_row)
            self.chapter_list.setCurrentItem(next_item)
            self.show_content(next_item)
        else:
            QMessageBox.warning(self, "提示", "已经是第一章节" if direction < 0 else "已经是最后一章节")


if __name__ == '__main__':
                app = QApplication(sys.argv)
                search_window = NovelSearchWindow()
                sys.exit(app.exec_())