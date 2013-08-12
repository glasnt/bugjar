"""A module containing a visual representation of the connection

This is the "View" of the MVC world.
"""
import os
from Tkinter import *
from tkFont import *
from ttk import *
import tkMessageBox

from bugjar.widgets import ReadOnlyCode
from bugjar.connection import ConnectionNotBootstrapped, UnknownBreakpoint


class DebuggerCode(ReadOnlyCode):
    def __init__(self, *args, **kwargs):
        print args, kwargs
        self.debugger = kwargs.pop('debugger')
        ReadOnlyCode.__init__(self, *args, **kwargs)

        # Set up styles for line numbers
        self.lines.tag_configure('enabled',
            background='red'
        )

        self.lines.tag_configure('disabled',
            background='gray'
        )

        self.lines.tag_configure('ignored',
            background='green'
        )

        self.lines.tag_configure('temporary',
            background='pink'
        )

    def enable_breakpoint(self, line, temporary=False):
        self.lines.tag_remove('disabled',
            '%s.0' % line,
            '%s.0' % (line + 1)
        )
        self.lines.tag_remove('ignored',
            '%s.0' % line,
            '%s.0' % (line + 1)
        )
        if temporary:
            self.lines.tag_remove('enabled',
                '%s.0' % line,
                '%s.0' % (line + 1)
            )
            self.lines.tag_add('temporary',
                '%s.0' % line,
                '%s.0' % (line + 1)
            )
        else:
            self.lines.tag_remove('temporary',
                '%s.0' % line,
                '%s.0' % (line + 1)
            )
            self.lines.tag_add('enabled',
                '%s.0' % line,
                '%s.0' % (line + 1)
            )

    def disable_breakpoint(self, line):
        self.lines.tag_remove('enabled',
            '%s.0' % line,
            '%s.0' % (line + 1)
        )
        self.lines.tag_remove('ignored',
            '%s.0' % line,
            '%s.0' % (line + 1)
        )
        self.lines.tag_remove('temporary',
            '%s.0' % line,
            '%s.0' % (line + 1)
        )
        self.lines.tag_add('disabled',
            '%s.0' % line,
            '%s.0' % (line + 1)
        )

    def clear_breakpoint(self, line):
        self.lines.tag_remove('enabled',
            '%s.0' % line,
            '%s.0' % (line + 1)
        )
        self.lines.tag_remove('disabled',
            '%s.0' % line,
            '%s.0' % (line + 1)
        )
        self.lines.tag_remove('ignored',
            '%s.0' % line,
            '%s.0' % (line + 1)
        )
        self.lines.tag_remove('temporary',
            '%s.0' % line,
            '%s.0' % (line + 1)
        )

    def on_line_double_click(self, line):
        "When a line number is double clicked, set a breakpoint"
        print "Toggle breakpoint"
        try:
            bp = self.debugger.breakpoint((self.current_file, line))
            if bp.enabled:
                self.debugger.disable_breakpoint(bp)
            else:
                self.debugger.enable_breakpoint(bp)
        except UnknownBreakpoint:
            self.debugger.create_breakpoint(self.current_file, line)
        except ConnectionNotBootstrapped:
            print "Connection not yet configured"

    def on_code_variable_double_click(self, var):
        "When a variable is double clicked, ..."
        pass


class MainWindow(object):
    def __init__(self, root, debugger):
        '''
        -----------------------------------------------------
        | main button toolbar                               |
        -----------------------------------------------------
        |       < ma | in content area >      |             |
        |            |                        |             |
        | File list  | File name              | Inspector   |
        | (stack/    | Code area              |             |
        | breakpnts) |                        |             |
        |            |                        |             |
        |            |                        |             |
        -----------------------------------------------------
        |     status bar area                               |
        -----------------------------------------------------

        '''

        self.debugger = debugger
        # Associate the debugger with this view.
        self.debugger.view = self

        # Root window
        self.root = root
        self.root.title('Bugjar')
        self.root.geometry('1024x768')

        # Prevent the menus from having the empty tearoff entry
        self.root.option_add('*tearOff', FALSE)
        # Catch the close button
        self.root.protocol("WM_DELETE_WINDOW", self.on_quit)
        # Catch the "quit" event.
        self.root.createcommand('exit', self.on_quit)

        # Setup the menu
        self._setup_menubar()

        # Set up the main content for the window.
        self._setup_button_toolbar()
        self._setup_main_content()
        self._setup_status_bar()

        # Now configure the weights for the root frame
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=0)
        self.root.rowconfigure(1, weight=1)
        self.root.rowconfigure(2, weight=0)

        # FIXME - set up some initial content.
        self.stack_list.insert('', 'end', text='file1.py', values=('123',))

        self.breakpoint_list.insert('', 'end', text='breakpoint1.py', values=('456',))

        debugger.start()
        print "STARTED"
        # Queue the first progress handling event
        # self.root.after(100, self.on_progress)



    ######################################################
    # Internal GUI layout methods.
    ######################################################

    def _setup_menubar(self):
        # Menubar
        self.menubar = Menu(self.root)

        # self.menu_Apple = Menu(self.menubar, name='Apple')
        # self.menubar.add_cascade(menu=self.menu_Apple)

        self.menu_file = Menu(self.menubar)
        self.menubar.add_cascade(menu=self.menu_file, label='File')

        self.menu_edit = Menu(self.menubar)
        self.menubar.add_cascade(menu=self.menu_edit, label='Edit')

        # self.menu_help = Menu(self.menubar, name='help')
        # self.menubar.add_cascade(menu=self.menu_help)

        # self.menu_Apple.add_command(label='Test', command=self.cmd_dummy)

        # self.menu_file.add_command(label='New', command=self.cmd_dummy, accelerator="Command-N")
        # self.menu_file.add_command(label='Open...', command=self.cmd_dummy)
        # self.menu_file.add_command(label='Close', command=self.cmd_dummy)

        # self.menu_edit.add_command(label='New', command=self.cmd_dummy)
        # self.menu_edit.add_command(label='Open...', command=self.cmd_dummy)
        # self.menu_edit.add_command(label='Close', command=self.cmd_dummy)

        # self.menu_help.add_command(label='Test', command=self.cmd_dummy)

        # last step - configure the menubar
        self.root['menu'] = self.menubar

    def _setup_button_toolbar(self):
        '''
        The button toolbar runs as a horizontal area at the top of the GUI.
        It is a persistent GUI component
        '''

        # Main toolbar
        self.toolbar = Frame(self.root)
        self.toolbar.grid(column=0, row=0, sticky=(W, E))

        # Buttons on the toolbar
        self.run_button = Button(self.toolbar, text='Run', command=self.cmd_run)
        self.run_button.grid(column=0, row=0)

        self.step_button = Button(self.toolbar, text='Step', command=self.cmd_step)
        self.step_button.grid(column=1, row=0)

        self.next_button = Button(self.toolbar, text='Next', command=self.cmd_next)
        self.next_button.grid(column=2, row=0)

        self.return_button = Button(self.toolbar, text='Return', command=self.cmd_return)
        self.return_button.grid(column=3, row=0)

        self.toolbar.columnconfigure(0, weight=0)
        self.toolbar.rowconfigure(0, weight=0)

    def _setup_main_content(self):
        '''
        Sets up the main content area. It is a persistent GUI component
        '''

        # Main content area
        self.content = PanedWindow(self.root, orient=HORIZONTAL)
        self.content.grid(column=0, row=1, sticky=(N, S, E, W))

        # Create subregions of the content
        self._setup_file_lists()
        self._setup_code_area()
        self._setup_inspector()

        # Set up weights for the left frame's content
        self.content.columnconfigure(0, weight=1)
        self.content.rowconfigure(0, weight=1)

        self.content.pane(0, weight=1)
        self.content.pane(1, weight=2)
        self.content.pane(2, weight=1)

    def _setup_file_lists(self):

        self.file_notebook = Notebook(self.content, padding=(0, 5, 0, 5))
        self.content.add(self.file_notebook)

        self.stack_list = Treeview(self.content)
        self.stack_list.grid(column=0, row=0, sticky=(N, S, E, W))
        self.stack_list['columns'] = ('line',)
        self.stack_list.column('line', width=100, anchor='center')
        self.stack_list.heading('line', text='Line')
        self.file_notebook.add(self.stack_list, text='Stack')

        self.breakpoint_list = Treeview(self.content)
        self.breakpoint_list.grid(column=0, row=0, sticky=(N, S, E, W))
        self.breakpoint_list['columns'] = ('line',)
        self.breakpoint_list.column('line', width=100, anchor='center')
        self.breakpoint_list.heading('line', text='Line')
        self.file_notebook.add(self.breakpoint_list, text='Breakpoints')

    def _setup_code_area(self):
        self.code_frame = Frame(self.content)
        self.code_frame.grid(column=1, row=0, sticky=(N, S, E, W))

        # Label for current file
        self.current_file = StringVar()
        self.current_file_label = Label(self.code_frame, textvariable=self.current_file)
        self.current_file_label.grid(column=0, row=0, sticky=(W, E))

        # Code display area
        self.code = DebuggerCode(self.code_frame, debugger=self.debugger)
        self.code.grid(column=0, row=1, sticky=(N, S, E, W))

        # Set up weights for the code frame's content
        self.code_frame.columnconfigure(0, weight=1)
        self.code_frame.rowconfigure(0, weight=0)
        self.code_frame.rowconfigure(1, weight=1)

        self.content.add(self.code_frame)

    def _setup_inspector(self):
        self.inspector_tree = Treeview(self.content)
        self.inspector_tree.grid(column=2, row=0, sticky=(N, S, E, W))

        self.content.add(self.inspector_tree)

    def _setup_status_bar(self):
        # Status bar
        self.statusbar = Frame(self.root)
        self.statusbar.grid(column=0, row=2, sticky=(W, E))

        # Current status
        self.run_status = StringVar()
        self.run_status_label = Label(self.statusbar, textvariable=self.run_status)
        self.run_status_label.grid(column=0, row=0, sticky=(W, E))
        self.run_status.set('Not running')

        # Main window resize handle
        self.grip = Sizegrip(self.statusbar)
        self.grip.grid(column=1, row=0, sticky=(S, E))

        # Set up weights for status bar frame
        self.statusbar.columnconfigure(0, weight=1)
        self.statusbar.columnconfigure(1, weight=0)
        self.statusbar.rowconfigure(0, weight=0)

    ######################################################
    # Utility methods for controlling content
    ######################################################

    def show_file(self, filename, line=None, breakpoints=None, refresh=False):
        """Show the content of the nominated file.

        If specified, line is the current line number to highlight. If the
        line isn't currently visible, the window will be scrolled until it is.

        breakpoints is a list of line numbers that have current breakpoints.

        If refresh is true, the file will be reloaded and redrawn.

        If the code was reloaded and redrawn, return True
        """
        path, name = os.path.split(filename)

        # Set the filename label for the current file
        self.current_file.set('%s (%s)' % (name, path))

        # Show the contents of the current file
        return self.code.show(filename=filename, line=line, refresh=refresh)

    def set_current_line(self, line):
        """Highlight a specific line of the current file.

        If line==None, the current line marker will be removed.
        """
        self.show_file(self.code.current_file, line=line)

    ######################################################
    # TK Main loop
    ######################################################

    def mainloop(self):
        self.root.mainloop()

    ######################################################
    # TK Command handlers
    ######################################################

    def on_quit(self):
        "Quit the debugger"
        self.debugger.stop()
        self.root.quit()

    def cmd_run(self):
        ""
        self.debugger.do_run()

    def cmd_step(self):
        self.debugger.do_step()

    def cmd_next(self):
        self.debugger.do_next()

    def cmd_return(self):
        self.debugger.do_return()

    ######################################################
    # Handlers for debugger responses
    ######################################################

    def on_stack(self, stack):
        "A report of a new stack"
        print "STACK UPDATE FOUND"
        if len(stack) > 0:
            line = stack[-1][0]
            filename = stack[-1][1]['filename']
            print filename, line
            file_change = self.show_file(filename=filename, line=line)

            # If there are breakpoints for this file, show them
            if file_change:
                for bp in self.debugger.breakpoints(filename).values():
                    if bp.enabled:
                        self.code.enable_breakpoint(bp.line)
                    else:
                        self.code.disable_breakpoint(bp.line)

        else:
            # No current frame (probably end of execution),
            # so clear the current line marker
            self.set_current_line(None)

    def on_line(self, filename, line):
        "A single line of code has been executed"
        self.run_status.set('Line (%s:%s)' % (filename, line))

    def on_call(self, args):
        "A callable has been invoked"
        self.run_status.set('Call: %s' % args)

    def on_return(self, retval):
        "A callable has returned"
        self.run_status.set('Return: %s' % retval)

    def on_exception(self, **kwargs):
        "An exception has been raised"
        print "EXCEPTION FOUND"
        print kwargs
        self.run_status.set('Exception')

    def on_restart(self, source):
        "The code has finished running, and will start again"
        self.run_status.set('Not running')
        tkMessageBox.showinfo(message='Program has finished, and will restart.')

    def on_info(self, message):
        "The debugger needs to inform the user of something"
        tkMessageBox.showinfo(message=message)

    def on_warning(self, message):
        "The debugger needs to warn the user of something"
        tkMessageBox.showwarning(message=message)

    def on_error(self, message):
        "The debugger needs to report an error"
        tkMessageBox.showerror(message=message)

    def on_breakpoint_enable(self, bp):
        "A breakpoint has been enabled in the debugger"
        print "enable breakpoint", bp
        if bp.filename == self.code.current_file:
            print "Enable break in current file"
            self.code.enable_breakpoint(bp.line, temporary=bp.temporary)
        else:
            print "Enable break in other file"

    def on_breakpoint_disable(self, bp):
        "A breakpoint has been disabled in the debugger"
        print "disable breakpoint", bp
        if bp.filename == self.code.current_file:
            print "Disable break in current file"
            self.code.disable_breakpoint(bp.line)
        else:
            print "Disable break in other file"

    def on_breakpoint_ignore(self, bp, count):
        print "ignore breakpoint", bp, count, 'iterations'
        if bp.filename == self.code.current_file:
            print "Ignore break in current file, count %s" % count
            self.code.ignore_breakpoint(bp.line)
        else:
            print "Ignore break in other file, count %s" % count

    def on_breakpoint_clear(self, bp):
        "A breakpoint has been cleared in the debugger"
        print "clear breakpoint", bp
        if bp.filename == self.code.current_file:
            print "Clear break in current file"
            self.code.clear_breakpoint(bp.line)
        else:
            print "Clear break in other file"