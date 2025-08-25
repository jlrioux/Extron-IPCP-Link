## Begin ControlScript Import --------------------------------------------------

from extronlib.engine import IpcpLink
link = IpcpLink('172.16.1.10','AVLAN')


from extronlib.system import Timer, Wait

from tools import EthernetModuleWrapper
from tools import IRInterfaceWrapper
from tools import UIDeviceWrapper
from tools import ProcessorDeviceWrapper
from tools import VirtualUI
from tools import ProgramLogSaver
from tools import DebugFileLogSaver,DebugServer
DebugFileLogSaver.SetProcessorAlias('processor0')

print('save debug logs to file? True')
DebugFileLogSaver.EnableLogging = True
print('save program logs to file? True')
ProgramLogSaver.EnableProgramLogSaver()
DebugServer.EnableDebugServer("AVLAN")

## End ControlScript Import ----------------------------------------------------
##
## Begin User Import -----------------------------------------------------------
from opto_vp_UHD60_v1_0_1_0 import DeviceClass as projector_mod
## End User Import -------------------------------------------------------------
##
## Begin Device/Processor Definition -------------------------------------------
Processor = ProcessorDeviceWrapper('processor0',friendly_name='Processor')
## End Device/Processor Definition ---------------------------------------------

## Begin User Interface Definition  --------------------------------------------=
UIHost1 = UIDeviceWrapper('panel0',friendly_name='iPad')
UIHost2 = UIDeviceWrapper('panel1',friendly_name='Phone')

tp = VirtualUI(friendly_name='MainTP')
tp.AddPanel([UIHost1.Device,UIHost2.Device])
## End User Interface Definition  ----------------------------------------------

## Begin Communication Interface Definition ------------------------------------
dev_receiver = IRInterfaceWrapper(Processor.Device,'IRS1','AVReceiver.eir',friendly_name='AVR')
dev_projector = EthernetModuleWrapper(projector_mod,friendly_name='Projector')
dev_projector.Create_Device('192.168.1.244',2023,Model='UHD60')

receiver_cmds = ['Power','Cable','Media','Bluray','Game','Volume+','Volume-','Mute']
## End Communication Interface Definition --------------------------------------

def Initialize():
    tp.HideAllPopups()
    tp.ShowPage('Start Page')
    dev_projector.SubscribeStatus('ConnectionStatus',None,proj_online_event)
    dev_projector.SubscribeStatus('Power',None,proj_power_event)
    proj_poll_timer.Restart()


## Event Definitions -----------------------------------------------------------

''' PROJECTOR EVENTS AND SUBSCRIPTOINS '''
proj_power_state = ''
proj_desired_power_state = ''
proj_online_state = ''
proj_power_off_override = False
proj_power_busy = False
def proj_power_poll(timer,count):
    global proj_desired_power_state
    global proj_power_state
    global proj_online_state
    if 'Connected' in proj_online_state:
        if count % 2 == 0:
            dev_projector.Update('Power')
        elif count % 2 == 1:
            if proj_power_state != proj_desired_power_state and proj_desired_power_state != '':
                dev_projector.Set('Power',proj_desired_power_state)
    else:
        if count % 2 == 0:
            val = dev_projector.Connect(1)
            if 'Connected' in val:
                dev_projector.OnConnected()
proj_poll_timer = Timer(5,proj_power_poll)
proj_poll_timer.Stop()
def proj_online_event(command,value,qualifier):
    global proj_online_state
    proj_online_state = value
    if 'Connected' in value:
        tp.SetText(lbl_projector,'Projector\nStatus')
        proj_poll_timer.Restart()
    else:
        tp.SetText(lbl_projector,'Disconnected')
        proj_poll_timer.Stop()
def proj_power_event(command,value,qualifier):
    global proj_power_state
    global system_power_state
    proj_power_state = value
    states = {'On':1,'Off':0}
    tp.SetState(btn_projector_power,states[value])
    tp.SetText(btn_projector_power,value)
    if value == 'On' and system_power_state != 'On':
        system_power_state = 'On'
        tp.ShowPage('Main Page')
        tp.HideAllPopups()
        tp.SetState(btn_controls,0)
    elif value == 'Off' and system_power_state == '':
        system_power_state = 'Off'
        tp.ShowPage('Start Page')
    tp.HideAllPopups()

def proj_power_set(desired):
    global proj_desired_power_state
    global proj_power_busy
    proj_desired_power_state = desired
    if proj_desired_power_state != proj_power_state:
        tp.SetBlinking(btn_projector_power,'Medium',[0,2])
    if proj_power_busy:
        return
    proj_power_busy = True
    dev_projector.Set('Power',desired)
    @Wait(180)
    def w():
        global proj_power_busy
        proj_power_busy = False

## End Events Definitions-------------------------------------------------------
system_power_state = ''
def fn_power_system_on():
    global controls_showing
    global system_power_state
    system_power_state = 'On'
    controls_showing = False
    tp.SetState(btn_controls,0)
    tp.HideAllPopups()
    tp.ShowPage('Main Page')
    #starting up
    dev_receiver.PlayCount('Power')
    #proj_power_set('On')
def fn_power_system_off():
    global controls_showing
    global system_power_state
    system_power_state = 'Off'
    controls_showing = False
    tp.ShowPage('Start Page')
    tp.HideAllPopups()
    dev_receiver.PlayCount('Power')
    proj_power_set('Off')
    tp.SetState(btn_controls,0)


## Begin TP Events Definitions--------------------------------------------------
btn_start = 1
tp.AddButton(btn_start)
def fn_btn_welcome(button,state):
    fn_power_system_on()
tp.SetFunction(btn_start,fn_btn_welcome,'Pressed')

btn_shutdown = 4
tp.AddButton(btn_shutdown)
def fn_btn_shutdown(button,state):
    tp.ShowPopup('Power Confirm')
tp.SetFunction(btn_shutdown,fn_btn_shutdown,'Pressed')

btn_shutdown_cancel = 3
tp.AddButton(btn_shutdown_cancel)
def fn_btn_shutdown_cancel(button,state):
    tp.HidePopup('Power Confirm')
tp.SetFunction(btn_shutdown_cancel,fn_btn_shutdown_cancel,'Pressed')

btn_shutdown_confirm = 2
tp.AddButton(btn_shutdown_confirm)
def fn_btn_shutdown_confirm(button,state):
    fn_power_system_off()

tp.SetFunction(btn_shutdown_confirm,fn_btn_shutdown_confirm,'Pressed')

controls_showing = False
btn_controls = 5
tp.AddButton(btn_controls)
def fn_btn_controls(button,state):
    global controls_showing
    controls_showing = not controls_showing
    vals = {True:1,False:0}
    tp.SetState(btn_controls,vals[controls_showing])
    if controls_showing:
        tp.ShowPopup('Popup Controls')
    else:
        tp.HideAllPopups()
tp.SetFunction(btn_controls,fn_btn_controls,'Pressed')




lbl_projector = 100
tp.AddLabel(lbl_projector)
btn_projector_power = 101
tp.AddButton(btn_projector_power,holdTime=5)
def fn_btn_projector_power_held(button,state):
    tp.SetText(lbl_projector,'Reconnecting')
    dev_projector.Disconnect()
tp.SetFunction(btn_projector_power,fn_btn_projector_power_held,'Held')



btn_receiver_controls = list(range(51,58))
tp.AddButton(btn_receiver_controls,repeatTime=0.5)
def fn_btn_receiver_controls_pressed(button,state):
    dev_receiver.PlayCount(receiver_cmds[button.ID-51])
def fn_btn_receiver_controls_repeated(button,state):
    dev_receiver.PlayCount(receiver_cmds[button.ID-51])
tp.SetFunction(btn_receiver_controls,fn_btn_receiver_controls_pressed,'Pressed')
tp.SetFunction([56,57],fn_btn_receiver_controls_repeated,'Repeated')


Initialize()