#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2011 ~ 2012 Deepin, Inc.
#               2011 ~ 2012 Jack River
# 
# Author:     Jack River <ritksm@gmail.com>
# Maintainer: Jack River <ritksm@gmail.com>
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import gtk
import gobject


def parse_text(text):
    result = dict()
    index = 0
    for line in text.split(u"\n"):
        result[index] = line + u"\n"
        index += 1
    result[index-1] = result[index-1].rstrip(u"\n") # remove the line break that does not exist actually
    return result

class TextIter(gobject.GObject):
    """TextIter for TextBuffer"""

    def __init__(self, line_number = 0, text_buffer = None,
            line_offset = 0, text = u""):
        """
        Args:
            line_number : current line number
            text_buffer : text buffer object to which this iter belongs
            line_offset : offset in current line
            text : the whole text in text buffer
        """

        gobject.GObject.__init__(self) # super class init
        self.__line_number = line_number
        self.__text_buffer = text_buffer
        self.__line_offset = line_offset
        self.__text = parse_text(text)
        self.__line_text = self.__text[line_number]
        self.__is_valid = True

    def get_buffer(self):
        return self.__text_buffer

    def get_offset(self):
        offset = 0
        for x in range(0, self.get_line()):
            offset += len(self.__text[x])
        offset += self.get_line_offset()
        return offset

    def get_line_text(self):
        """return text of current line including \n"""
        return self.__text[self.get_line()]

    def get_line(self):
        return self.__line_number

    def get_line_offset(self):
        """return offset in utf8"""
        return self.__line_offset

    def get_line_index(self):
        """return offset in bytes"""
        return len(self.__line_text[0:self.__line_offset].encode("utf8"))

    def get_char(self):
        """return in Unicode-8 format"""
        return self.__line_text[self.__line_offset:self.__line_offset+1]

    def get_slice(self, end):
        """
        return a slice of text in Unicode-8 format
        """
        if end.get_line() == self.get_line():
            # in the same line
            if self.get_line_offset() < end.get_line_offset():
                return self.__line_text[self.get_line_offset():end.get_line_offset()]
        else:
            if end.get_line() < self.get_line():
                up = end
                down = self
            else:
                up = self
                down = end
            result = u""
            temp = up.get_line_text()
            result += temp[up.get_line_offset():len(temp)] # add first line after offset
            for x in range(up.get_line() + 1, down.get_line()):
                # add lines between
                up.forward_line()
                result += up.get_line_text()
            result += down.get_line_text()[0:down.get_line_offset()] # add last line before offset
            return result


    def get_text(self, end):
        """TODO:what is the difference between this and get_slice()?"""
        return self.get_slice(end)

    def has_tag(self):
        """TODO:return True if current location is tagged with tag"""
        return False

    def __is_editable_at_current_location(self):
        """
        TODO:return True if current location with tags is editable
        implemented only after self.has_tag is implemented
        """
        pass

    def __can_insert_at_current_location(self):
        """
        TODO:return True if text inserted at current location is editable
        implemented only after self.has_tag is implemented
        """

    def editable(self, default_setting):
        """return True is current offset is in an editable range"""
        if self.has_tag():
            return self.__is_editable_at_current_location()
        else:
            return default_setting

    def can_insert(self, default_editability):
        """return True is text inserted in current location is editable"""
        if self.has_tag():
            return self.__can_insert_at_current_location()
        else:
            return default_editability

    def get_chars_in_line(self):
        """return char count in Unicode-8 format in current line"""
        return len(self.__line_text)

    def get_bytes_in_line(self):
        """return byte count in current line"""
        return len(self.__line_text.encode("utf8"))

    def get_chars_in_iter(self):
        """return char count in Unicode-8 format in the whole text"""
        count = 0
        for x in range(0, len(self.__text.keys())):
            count += len(self.__text[x])
        return count

    def is_end(self):
        """return True if at the end of iter"""
        if self.get_offset() == self.get_chars_in_iter() + 1:
            return True
        else:
            return False

    def is_start(self):
        if self.get_offset() == 0:
            return True
        else:
            return False

    def forward_char(self):
        if not self.is_end():
            if self.get_char() == "\n":
                # at line end, go to the next line
                self.forward_line()
            else:
                self.__line_offset += 1
        else:
            # already at the end of iter
            pass
    
    def backward_char(self):
        if not self.is_start():
            if self.__line_offset == 0:
                # at line start
                self.backward_line()
            else:
                self.__line_offset -= 1
        else:
            # already at the start of iter
            pass

    def forward_line(self):
        if self.get_line() != len(self.__text.keys()):
            # not the last line
            self.__line_offset = 0
            self.__line_number += 1
            self.__line_text = self.__text[self.get_line()] # get new line text
        else:
            self.__line_offset = len(self.__text[self.get_line()]) # move to end of last line

    def backward_line(self):
        if self.get_line() != 0:
            # not the first line
            self.__line_number -= 1 # go to previous line
            self.__line_text = self.__text[self.get_line()] # get new line text
            self.__line_offset = len(self.__line_text) - 1 # minus one to ignore the \n
        else:
            self.__line_offset = 0 # move to start of first line

    def set_offset(self, offset):
        if offset <= self.get_chars_in_iter() + 1:
            self.__line_number = 0
            self.__line_offset = 0
            for x in range(0, offset):
                self.forward_char()
        else:
            raise Exception()

    def __goto_line(self, line):
        self.__line_number = line
        self.__line_text = self.__text[self.__line_number]
        self.__line_offset = 0 # move to line start

    def set_line(self, line):
        if line < 0:
            self.__goto_line(0)
        elif line < len(self.__text.keys()):
            self.__goto_line(line)
        else:
            self.__goto_line(len(self.__text.keys() - 1)) # go to the last line

    def __goto_line_offset(self, offset):
        self.__line_offset = offset

    def __goto_line_index(self, index):
        self.set_line_offset(len((self.get_line_text().encode("utf8")[0:index]).decode("utf8"))) # go to some index
        #TODO check this with gtk.TextIter

    def set_line_offset(self, offset):
        """The character offset must be less than or equal to the number of characters in the line"""
        if offset < 0 or offset > len(self.get_line_text()):
            raise Exception()
        else:
            self.__goto_line_offset(offset)

    def set_new_text(self, text, new_line_inserted):
        self.__text = parse_text(text)
        self.set_line(self.get_line() + new_line_inserted) # if there is u"\n" in text then there will be new lines
        self.__line_text = self.__text[self.get_line()]

    def set_line_index(self, index):
        """
        The given byte index must be at the start of a character, it can't be in the middle of a UTF-8 encoded character.
        We won't check for you here
        """
        self.__goto_line_index(index)

    def forward_to_end(self):
        while not self.is_end():
            self.forward_char()

    def forward_to_line_end(self):
        self.__line_offset = len(self.get_line_text())

    def in_range(self, start, end):
        """start and end must be in ascending order"""
        if start.get_line() > end.get_line():
            # start and end not in ascending order
            raise Exception()
        elif start.get_line() == end.get_line():
            if start.get_line() == self.get_line():
                if start.get_line_offset() <= self.get_line_offset() and self.get_line_offset() <= end.get_line_offset():
                    return True
                else:
                    return False
            else:
                if start.get_line() <= self.get_line() and self.get_line() <= end.get_line():
                    return True
                else:
                    return False

    def set_invalid(self):
        """set textiter to invalid mode"""
        self.__is_valid = False

gobject.type_register(TextIter)

class TextBuffer(gobject.GObject):

    __gsignals__ = {
        'insert-text': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (TextIter, str)),
    }

    def __init__(self, text = u""):
        gobject.GObject.__init__(self)
        self.__text = parse_text(text)
        self.__text_iter_list = list() # setup a list for textiter storage
        self.__cursor = (0, 0) # (line_offset, line)
    
    def get_line_count(self):
        return len(self.__text.keys())

    def get_char_count(self):
        result = 0
        for x in range(0,self.get_line_count()):
            result += len(self.__text[x])
        return result

    def get_line_text(self, line):
        return self.__text[line]

    def __set_iter_in_list_invalid(self, except_list = list(), some_iter = None):
        if some_iter == None:
            # delete multiple iter
            for ir in self.__text_iter_list:
                if ir not in except_list:
                    ir.set_invalid()
                    self.__text_iter_list.remove(ir)
        else:
            # delete single iter
            if some_iter in self.__text_iter_list:
                some_iter.set_invalid()
                self.__text_iter_list.remove(some_iter)

    def set_text(self, text):
        self.__text = parse_text(text)
        self.__set_iter_in_list_invalid()

    def get_text(self):
        result = u""
        for x in range(0, self.get_line_count()):
            result += self.__text[x]
        return result

    def do_insert_text(self, text_iter, text):
        """
        default handler fo insert-text
        we should do some real work inserting text here
        and revalidate the text_iter
        """
        line = text_iter.get_line()
        line_offset = text_iter.get_line_offset()
        old_line_text = self.get_line_text(line)
        new_text = self.get_text().replace(old_line_text, old_line_text[0:line_offset] + text + old_line_text[line_offset:len(old_line_text)])
        self.__text = parse_text(new_text) # insert and parse new self.__text
        # set new text for the textiter
        # new line will be automatically added in the set_text function, so only thing has to be done is providing the new line count
        text_iter.set_new_text(self.get_text(), text.count(u"\n"))
        # set new line offset, should be len(text.split("\n")[-1]) instead of len(text)
        text_iter.set_line_offset(line_offset + len(text.split("\n")[-1]))

    def get_iter_at_line(self, line):
        ir = TextIter(text = self.get_text(), line_number = line, line_offset = 0, text_buffer = self)
        self.__text_iter_list.append(ir) # add to textiter list
        return ir

    def insert_text(self, text_iter, text):
        self.__set_iter_in_list_invalid([text_iter,]) # set text iter invalid except this one because we can revalidate it by default
        self.emit("insert-text", text_iter, text)

    def insert_text_at_cursor(self, text):
        ir = self.get_iter_at_cursor()
        self.insert_text(ir, text)
        self.__set_iter_in_list_invalid(some_iter = ir)

    def get_iter_at_cursor(self):
        (line_offset, line) = self.__cursor
        ir = TextIter(text = self.get_text(), line_number = line, line_offset = line_offset) # create new textiter
        self.__text_iter_list.append(ir)
        return ir

    def get_slice(self, start, end):
        return start.get_slice(end)

    def insert_range(text_iter, start, end):
        """copy text between start and end (the order of start and end doesn't matter) form TextBuffer and inserts the copy at iter"""
        self.insert(text_iter, self.get_slice(start, end))




gobject.type_register(TextBuffer)

if __name__ == "__main__":
    tb = TextBuffer()
