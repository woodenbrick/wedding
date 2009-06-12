import time
import gtk
import gtk.glade
import pygtk
pygtk.require("2.0")
import sqlite3
import gobject
import datetime
import sys
import pango

def timer(future_time, end_string="until this timer runs out!", full=False):
    """future_time is a datetime object"""
    current_time = datetime.datetime.now()
    timedelta = future_time - current_time
    if full is False:
        day_str = "days" if timedelta.days > 1 else "day"
        return "%s %s %s" % (timedelta.days, day_str, end_string) 
    #convert seconds into hours, mins
    time_list = []
    time_names = ["day", "hour", "minute", "second"]
    time_list.append(timedelta.days)
    minutes = timedelta.seconds / 60 % 60
    time_list.append(timedelta.seconds / 60 / 24 )
    time_list.append(minutes)
    time_list.append(timedelta.seconds)
    #create string
    string = []
    for i in range(0, len(time_names)):
        pl = "s" if time_list[i] > 1 else ""
        if time_list[i] > 0:
            string.append(str(time_list[i]) + " " + time_names[i] + pl)
            return ", ".join(string) + " " + end_string



WEDDING_TIME = datetime.datetime(2009, 8, 15, 12, 0, 0)

class WeddingChecklist(object):
    
    def __init__(self):
        self.wTree = gtk.glade.XML("ui.glade")
        self.wTree.signal_autoconnect(self)
        self.db = sqlite3.Connection("checklist.sqlite")
        self.cursor = self.db.cursor()
        self.create_sql_tables()
        self.treeview = self.wTree.get_widget("checklist_treeview")
        self.liststore = gtk.ListStore(int, str, str, str, gobject.TYPE_BOOLEAN)
        items = self.cursor.execute("""select * from checklist""").fetchall()
        self.is_done = 0.0
        for item in items:
            self.liststore.append(item)
            if item[4] == True:
                self.is_done += 1
        self.selection_filter = self.liststore.filter_new()
        self.treeview.set_model(self.selection_filter)
        self.selection_filter.set_visible_func(self.check_selection_visibility)
        str_cols = ["id", "Item", "Category", "Sub Category"]
        for i, col_name in enumerate(str_cols):
            col = gtk.TreeViewColumn(col_name)
            cell = gtk.CellRendererText()
            col.pack_start(cell, False)
            if col_name == "Item":
                col.set_min_width(200)
                col.set_max_width(300)
            else:
                col.set_min_width(100)
                col.set_max_width(250)
            col.set_sizing(gtk.TREE_VIEW_COLUMN_GROW_ONLY)
            cell.props.wrap_mode = pango.WRAP_WORD_CHAR
            cell.props.wrap_width = 270
            col.set_attributes(cell, text=i)
            cell.set_property('editable', True)
            cell.connect('edited', self.edited, i)

            self.treeview.append_column(col)
            if col_name == "id":
                col.set_visible(False)
            
        col = gtk.TreeViewColumn("Done?")
        cell = gtk.CellRendererToggle()
        col.pack_start(cell, False)
        cell.set_property('activatable', True)
        cell.connect( 'toggled', self.on_item_checked, self.selection_filter)
        col.add_attribute(cell, "active", 4)
        self.treeview.append_column(col)
        
        self.change_view = gtk.combo_box_new_text()
        self.change_view.show()
        self.change_view.connect("changed", self.on_change_view, None)
        self.wTree.get_widget("hbox1").pack_start(self.change_view)
        items = ["All", "Not Done", "Done"]
        for item in items:
            self.change_view.append_text(item)
        self.change_view.set_active(0)
            
        self.new_category = gtk.combo_box_new_text()
        self.wTree.get_widget("hbox2").pack_start(self.new_category)
        items = ["Ceremony", "Reception", "Pinkies"]
        
        for item in items:
            self.new_category.append_text(item)
            
        sub_cat = ["Documents",
                 "Location",
                 "Decoration",
                 "Music",
                 "Food & Drink",
                 "Rituals/Traditions",
                 "Cars",
                 "Photos",
                 "Bride/Bridesmaids/Groom/Best man"]
        self.sub_categories = gtk.combo_box_new_text()
        self.wTree.get_widget("hbox2").pack_start(self.sub_categories)
        for cat in sub_cat:
            self.sub_categories.append_text(cat)
        self.sub_categories.show()
        self.sub_categories.set_active(0)
                 
        self.new_category.show()
        self.new_category.set_active(0)
        
        self.timer = gobject.timeout_add(600000, self.update_wedding_timer)
        self.update_wedding_timer()
        self.counter = self.cursor.execute("""SELECT count(*) FROM checklist""").fetchone()[0]
        self.update_progress_bar()
        
    def on_change_view(self, widget, *args):
        """Filter out results based on the contents of change_view"""
        self.show = self.change_view.get_active_text()
        self.selection_filter.refilter()
        
    
    def check_selection_visibility(self, model, iter):
        if self.show == "All":
            return True
        if self.show == "Not Done":
            return not model.get_value(iter, 4)
        if self.show == "Done":
            return model.get_value(iter, 4)
            
    def update_wedding_timer(self):
        self.wTree.get_widget("wedding_timer").set_text(timer(WEDDING_TIME, "to go!"))
    
    def update_progress_bar(self):
        try:
            fraction = (self.is_done / self.counter)
        except ZeroDivisionError:
            fraction = 0
        self.wTree.get_widget("progress_bar").set_text("%s out of %s items complete." % (int(self.is_done), self.counter))
        self.wTree.get_widget("progress_bar").set_fraction(fraction)

    
    def on_item_checked(self, cell, path, model):
        path = model.convert_path_to_child_path(path)
        self.liststore[path][4] = not self.liststore[path][4]
        if self.liststore[path][4] == True:
            self.is_done += 1
        else:
            self.is_done -= 1
        self.cursor.execute("""update checklist set is_done=? WHERE id=?""", (
            self.liststore[path][4], self.liststore[path][0]))
        self.db.commit()
        self.update_progress_bar()
    
    def edited(self, cell, path, new_text, column):
        path = self.selection_filter.convert_path_to_child_path(path)
        items = ["id", "item", "category", "sub_category"]
        query = """update checklist set %s='%s' WHERE id=%s""" % (items[column],
                                                                        new_text,
                                                                        self.liststore[path][0])
        self.cursor.execute(query)
        self.db.commit()
        self.liststore[path][column] = new_text
        
    def on_new_item_key_press_event(self, widget, key):
        if key.keyval == 65293:
            self.on_add_item()
    
    
    def on_add_item(self, *args):
        new_item = self.wTree.get_widget("new_item").get_text()
        new_category = self.new_category.get_active_text()
        sub_category = self.sub_categories.get_active_text()
        self.cursor.execute("""INSERT INTO checklist (item,
                               category, sub_category) VALUES (?, ?, ?)""", (
                                new_item, new_category, sub_category)
                               )
        self.db.commit()
        self.liststore.append([self.cursor.lastrowid, new_item, new_category, sub_category, 0])
        self.counter += 1
        self.update_progress_bar()
        self.wTree.get_widget("new_item").set_text("")
        vadj = self.wTree.get_widget("scrolledwindow1").get_vadjustment()
        vadj.value = -1 #vadj.upper
        
    def create_sql_tables(self):
        query = """create table if not exists checklist (
            `id` integer PRIMARY KEY,
            `item` text,
            `category` varchar(50),
            `sub_category` varchar(50),
            `is_done` boolean default 0
        )"""
        self.cursor.execute(query)
        self.db.commit()
        
    def gtk_main_quit(self, *args):
        gtk.main_quit()
        
WeddingChecklist()
gtk.main()