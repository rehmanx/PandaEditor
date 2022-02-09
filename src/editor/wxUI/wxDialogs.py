import wx


class DialogManager:
    """"Manages creation and destruction of dialogues"""

    def __init__(self):
        self.dialogues = {"YesNoDialog": WxYesNoDialog,
                          "TextEntryDialog": WxTextEntryDialog
                          }

        # list of all active dialogues
        self.active_dialogues = []

    def create_dialog(self, dialog_type: str, *args, **kwargs):
        if dialog_type in self.active_dialogues:
            pass

        elif dialog_type in self.dialogues.keys():
            dialog = self.dialogues[dialog_type]
            dialog = dialog(*args, **kwargs)

            dialog.create()
            dialog.Center()
            dialog.Show()

        else:
            print("dialogue type: {0} not found".format(dialog_type))


class WxCustomDialog(wx.Frame):
    def __init__(self, _title, _close_method=None, *args, **kwargs):
        super(WxCustomDialog, self).__init__(parent=None, title=_title)

        # method to be called when ok/yes button of dialog is clicked
        self.ok_call = kwargs.pop("ok_call", None)

        # method to be called when cancel button of dialog is clicked
        self.cancel_call = kwargs.pop("cancel_call", None)

        # method to be called when dialog is closed without pressing close button
        self.close_call = kwargs.pop("close_call", None)

        self.descriptor_text = kwargs.pop("descriptor_text", None)

        self.ok_button_id = None
        self.cancel_button_id = None

        # set min, max and current sizes for this dialog
        self.SetMinSize((300, 140))
        self.SetMaxSize((450, 140))
        self.SetSize((400, 140))

        self.Bind(wx.EVT_SIZE, self.on_event_size)
        self.Bind(wx.EVT_CLOSE, self.on_event_close)

    '''# method to be called when dialog is closed without pressing close button'''

    def set_close_call(self, foo):
        self.close_call = foo

    '''set method to be called when ok/yes button of dialog is clicked'''

    def set_ok_call(self, foo):
        self.ok_call = foo

    '''set method to be called when cancel button of dialog is clicked'''

    def set_cancel_call(self, foo):
        self.cancel_call = foo

    '''create buttons/ widgets for this dialog, this method must be called before calling dialog.Show()'''

    def create(self):
        pass

    def on_ok_button(self, event):
        event.Skip()

    def on_cancel_button(self, event):
        if self.cancel_call is not None:
            self.cancel_call()
        self.Close()
        event.Skip()

    def on_event_size(self, event):
        event.Skip()

    def on_event_close(self, event):
        event.Skip()


class WxTextEntryDialog(WxCustomDialog):
    def __init__(self, *args, **kwargs):
        WxCustomDialog.__init__(self, *args, **kwargs)

        if self.descriptor_text is None:
            self.descriptor_text = "Enter text"

        self.starting_text = kwargs.pop("starting_text", "")

        self.wx_text_ctrl = None

    def on_ok_button(self, event):
        if self.ok_call is not None:
            self.ok_call(self.wx_text_ctrl.GetValue())
        self.Close()
        event.Skip()

    def create(self):
        panel = wx.Panel(self)

        text = wx.StaticText(panel, label=self.descriptor_text)
        self.wx_text_ctrl = wx.TextCtrl(panel)
        self.wx_text_ctrl.SetValue(self.starting_text)

        self.ok_button_id = wx.NewId()
        self.cancel_button_id = wx.NewId()

        static_line = wx.StaticLine(panel, style=wx.LI_HORIZONTAL)

        button_ok = wx.Button(panel, label="Ok", size=(90, 28), id=self.ok_button_id)
        button_close = wx.Button(panel, label="Close", size=(90, 28), id=self.cancel_button_id)

        v_sizer = wx.BoxSizer(wx.VERTICAL)
        v_sizer.Add(text, flag=wx.LEFT | wx.TOP | wx.RIGHT | wx.EXPAND, border=5)
        v_sizer.Add(self.wx_text_ctrl, flag=wx.LEFT | wx.TOP | wx.RIGHT | wx.EXPAND, border=5)

        h_sizer = wx.BoxSizer(wx.HORIZONTAL)
        h_sizer.Add(button_ok, flag=wx.TOP, border=5)
        h_sizer.Add(button_close, flag=wx.TOP, border=5)

        v_sizer.AddSpacer(7)
        v_sizer.Add(static_line, flag=wx.RIGHT | wx.LEFT | wx.EXPAND, border=5)

        v_sizer.AddSpacer(8)
        v_sizer.Add(h_sizer, flag=wx.ALIGN_RIGHT | wx.RIGHT, border=5)

        panel.SetSizer(v_sizer)

        self.Bind(wx.EVT_BUTTON, self.on_ok_button, id=self.ok_button_id)
        self.Bind(wx.EVT_BUTTON, self.on_cancel_button, id=self.cancel_button_id)


class WxYesNoDialog(WxCustomDialog):
    def __init__(self, *args, **kwargs):
        WxCustomDialog.__init__(self, *args, **kwargs)

        if self.descriptor_text is None:
            self.descriptor_text = "Are you sure you want to perform this action ?"

        self.wx_text_ctrl = None

        # set min, max and current sizes for this dialog
        self.SetMinSize((300, 115))
        self.SetMaxSize((450, 115))
        self.SetSize((400, 115))

    def on_ok_button(self, event):
        if self.ok_call is not None:
            self.ok_call()

        self.Close()
        event.Skip()

    def create(self):
        panel = wx.Panel(self)

        text = wx.StaticText(panel, label=self.descriptor_text)

        self.ok_button_id = wx.NewId()
        self.cancel_button_id = wx.NewId()

        button_ok = wx.Button(panel, label="Yes", size=(90, 28), id=self.ok_button_id)
        button_close = wx.Button(panel, label="No", size=(90, 28), id=self.cancel_button_id)

        static_line = wx.StaticLine(panel, style=wx.LI_HORIZONTAL)

        v_sizer = wx.BoxSizer(wx.VERTICAL)
        v_sizer.Add(text, flag=wx.LEFT | wx.TOP | wx.RIGHT | wx.EXPAND, border=5)

        h_sizer = wx.BoxSizer(wx.HORIZONTAL)
        h_sizer.Add(button_ok, flag=wx.TOP, border=5)
        h_sizer.Add(button_close, flag=wx.TOP, border=5)

        v_sizer.AddSpacer(7)
        v_sizer.Add(static_line, flag=wx.RIGHT | wx.LEFT | wx.EXPAND, border=5)

        v_sizer.AddSpacer(8)

        v_sizer.Add(h_sizer, flag=wx.ALIGN_RIGHT | wx.RIGHT, border=5)

        panel.SetSizer(v_sizer)

        self.Bind(wx.EVT_BUTTON, self.on_ok_button, id=self.ok_button_id)
        self.Bind(wx.EVT_BUTTON, self.on_cancel_button, id=self.cancel_button_id)
