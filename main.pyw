from manager import *
from set_connect import *
from tkinter import *
from tkinter import ttk
#from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.scheduler import Scheduler
from datetime import datetime, timedelta
from PIL import Image as PilImage
from PIL import ImageTk
import xml.etree.ElementTree as ET
import time
import os
import requests

class Main:
    def __init__(self, title = "Добро пожаловать! vMixSheduler", icon=r"res/pencil.ico"):
        self.root = Tk()
        self.root.title(title)
        self.i = 0
        self.tree = ttk.Treeview(self.root, columns=('Title', 'GUID', 'Duration', 'Type', 'Start', 'End'), height=15, show='headings')
        self.url = '127.0.0.1'
        self.port = '8088'
        self.guid_key = ''

        self.sched = Scheduler()
        self.sched.start()
        self.job_start = ''
        self.job_end = ''
        self.job_next = ''
        self.event_start_items = []
        self.event_next = ''
        # Обработка иконки для кнопок
        img_pencl = PilImage.open(r"res/manager.png")
        img_pencl = img_pencl.resize((25,25), PilImage.ANTIALIAS)
        self.icon_mng =  ImageTk.PhotoImage(img_pencl)
        img_clock = PilImage.open(r"res/update.png")
        img_clock = img_clock.resize((25,25), PilImage.ANTIALIAS)
        self.icon_clc =  ImageTk.PhotoImage(img_clock)
        img_tune = PilImage.open(r"res/tune.png")
        img_tune = img_tune.resize((25,25), PilImage.ANTIALIAS)
        self.icon_tun =  ImageTk.PhotoImage(img_tune)
        
        # Кнопки в топ баре
        if icon:
            self.root.iconbitmap(icon)
        
    def run(self):
        self.draw_wigets()
        self.get_connect_to_vmix()
        self.cmd()
        self.root.mainloop()

    def get_connect_to_vmix(self):
        try:
            root = ET.parse('res/conf.xml').getroot()
            root_find = root.findall('setting/')
        except:
            root = ET.parse('res/conf_origin.xml').getroot()
            root_find = root.findall('setting/')
        for tag in root_find:
            url = tag.get('url')
            port = tag.get('port')
            key = tag.get('key')
            self.url = url
            self.port = port
            self.guid_key = key

    def cmd(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        self.i = 0

        self.get_connect_to_vmix()
        
        root = ET.parse('temp/last_shedule.xml').getroot()
        root_find = root.findall('events/')
        now = datetime.now()
        for y in root_find:
            key = y.get('guid')
            time = y.get('duration')
            type_i = y.get('type')
            start = y.get('start')
            end = y.get('end')
            count_time = datetime.strptime(str(start), "%Y-%m-%d %H:%M:%S")
            if now < count_time: 
                self.tree.insert('', 'end', text="Item_"+str(self.i), values=(y.text, key, time, type_i, start, end))
            else:
                pass
        
        messagebox.showinfo("Информация: ", f"Планировщик успешно обновлен!")
        self.push_to_shedule()
                
    def del_to_tree(self):
        item = self.tree.get_children()[0]
        self.tree.delete(item)

    def push_to_shedule(self):
        try:
            children = self.tree.get_children()[0]

            self.event_start_items = [str(self.tree.item(children)['values'][1]), str(self.tree.item(children)['values'][2]), str(self.tree.item(children)['values'][4]), str(self.tree.item(children)['values'][5])]
            
            try:
                self.event_next = str(self.tree.item(self.tree.get_children()[1])['values'][4])
            except:
                self.event_next = str(self.tree.item(children)['values'][5])
            # Определяем время задачи
            time_start = datetime.strptime(str(self.event_start_items[2]) , "%Y-%m-%d %H:%M:%S")
            time_end = datetime.strptime(str(self.event_start_items[3]) , "%Y-%m-%d %H:%M:%S")
            time_next = datetime.strptime(str(self.event_next) , "%Y-%m-%d %H:%M:%S") - timedelta(seconds=10)

            self.job_start = self.sched.add_date_job(self.start_shade, time_start)
            self.job_end = self.sched.add_date_job(self.end_shade, time_end)
            self.job_next = self.sched.add_date_job(self.next_shade, time_next)
        except IndexError:
            messagebox.showinfo("Информация: ", f"Задачи как бы все!=) Ну или просто пусто")

    def start_shade(self):
        key = self.event_start_items[0]
        duration = datetime.time(datetime.strptime(str(self.event_start_items[1]), "%H:%M:%S"))
        req = timedelta(hours=int(duration.hour), minutes=int(duration.minute), seconds=int(duration.second)+1) / timedelta(milliseconds=1)
        inp = (
            ('Function', 'Fade'),
            ('Duration', str(int(req))),
            ('Input', key),
        )
        res_fade = requests.get('http://'+str(self.url)+':'+str(self.port)+'/API', params=inp)
    
    def end_shade(self):
        key = self.event_start_items[0]
        inp = (
            ('Function', 'Cut'),
        )
        irestart = (
            ('Function', 'Restart'),
            ('Input', key),
        )
        res_fade = requests.get('http://'+str(self.url)+':'+str(self.port)+'/API', params=inp)
        res_restart = requests.get('http://'+str(self.url)+':'+str(self.port)+'/API', params=irestart)
    
    def next_shade(self):
        self.del_to_tree()
        try:
            time.sleep(1)
            self.push_to_shedule()
        except:
            messagebox.showinfo("Информация: ", f"Задачи как бы все!=) Ну или просто пусто")

    def run_manger(self):
        Manager(self.root)

    def run_connect(self):
        SetConnect(self.root)

    def draw_wigets(self):
        self.draw_menu()
        self.draw_tree()
        
    def draw_tree(self):
        self.tree.column('Title', width=150, anchor=CENTER)
        self.tree.column('GUID', width=200, anchor=CENTER)
        self.tree.column('Duration', width=170, anchor=CENTER)
        self.tree.column('Type', width=100, anchor=CENTER)
        self.tree.column('Start', width=200, anchor=CENTER)
        self.tree.column('End', width=200, anchor=CENTER)

        self.tree.heading('Title',text='Input')
        self.tree.heading('GUID',text='Ключ')
        self.tree.heading('Duration',text='Проболжительность')
        self.tree.heading('Type',text='Тип')
        self.tree.heading('Start',text='Начало')
        self.tree.heading('End',text='Конец')
        self.tree.pack(side=LEFT, expand="yes", fill=BOTH)

    def draw_menu(self):
        # menu_bar
        menubar = Menu(self.root)
        fileMenu = Menu(self.root, tearoff=0, bg='black')
        fileMenu.add_command(label="Менеджер", command=self.run_manger)
        toolbar = Frame(self.root, bd=1, relief=RAISED)
        
        # Open Manager
        open_mng = Button(
            toolbar, image=self.icon_mng, relief=FLAT,
            command=self.run_manger
        )
        open_mng.image = self.icon_mng
        open_mng.pack(side=LEFT, padx=2, pady=2)
        # Update
        upd = Button(
            toolbar, image=self.icon_clc, relief=FLAT,
            command=self.cmd
        )
        upd.image = self.icon_clc
        upd.pack(side=LEFT, padx=2, pady=2)
        # config
        tune = Button(
            toolbar, image=self.icon_tun, relief=FLAT,
            command=self.run_connect
        )
        tune.image = self.icon_tun
        tune.pack(side=LEFT, padx=2, pady=2)
        # Compil
        toolbar.pack(side=TOP, fill=X)
        self.root.configure(menu=menubar)

if __name__ == "__main__":
    root = Main()
    #root.run_manger()
    root.run()