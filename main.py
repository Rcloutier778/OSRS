import sys
import os
import java.awt.Toolkit # only once per script

sys.path.append(os.getcwd() + '\\sikulixapi.jar\\Lib')
import datetime
from sikuli import *

import signal
import time
import operator
import random
random = random.SystemRandom()
import math

import threading

LAST_INV_BBOX = Region(867, 948, 30, 30)
FIRST_INV_BBOX = Region(714, 678, 30, 30)
INV_ICON_BBOX = Region(793, 626, 25, 34)
BANK_FIRST_ITEM_BBOX = Region(92, 139, 27, 22)
BANK_TITLE_BBOX = Region(142, 36, 310, 35)

def _press_key(key):
    '''
    Press a key
        https://stackoverflow.com/questions/22505698/what-is-a-typical-keypress-duration
        Says that standard keypress is 50 ms to 300 ms
    :param key:
    :return:
    '''
    keyDown(key)
    _wait(0.05, 0.3)
    keyUp(key)
    _wait(0.8, 2)

def _assert_standing_at_bank():
    '''
    Assert the player (you) is standing in a marked tile.
    Assumes that the camera is verticle and zoomed in
    Checks the 4 corners for the yellow tile highlight right angle
    :return:
    '''
    #TODO corners change depending on how you got to that tile
    corners = {
        'NW': Region(383, 395, 43, 41),
        'NE': Region(572, 387, 54, 62),
        'SE': Region(565, 586, 63, 57),
        'SW': Region(387, 580, 36, 53),
    }

    matches = 0
    for corner, region in corners.items():
        pattern = Pattern(os.getcwd() + r'\images\%s_corner_marker.png' % corner)
        pattern.similar(0.95)

        if region.exists(pattern, 0):
            matches += 1

    assert matches >= 3, '%d corners were not found!' % (4 - matches)


def _assert_player_in_tile():
    '''
    Assert the player (you) is standing in a marked tile.
    Assumes that the camera is verticle and zoomed in
    Checks the 4 corners for the yellow tile highlight right angle
    :return:
    '''
    #TODO currently setup for mining south orientation!!
    corners = {
        'NW' : Region(383, 441, 44, 43),
        'NE' : Region(571, 438, 54, 51),
        'SE' : Region(568, 619, 56, 62),
        'SW' : Region(379, 632, 48, 48),
    }
    
    matches  = 0
    for corner, region in corners.items():
        pattern = Pattern(os.getcwd() + r'\images\%s_corner_marker.png' % corner)
        pattern.similar(0.95)

        if region.exists(pattern, 0):
            matches += 1

    assert matches >=3 , '%d corners were not found!' % (4-matches)
    
    
def _ge_click_banker(bank_title):
    '''
    
    :param bank_title: Title of the bank inventory screen
    :return:
    '''
    bank_bbox = Region(695, 481, 45, 51)
    blank_bank_bbox = Region(158, 284, 344, 354)
    
    for bankAttempt in range(3):
        _assert_standing_at_bank()
        randomCoords(bank_bbox).click()
        _wait(1, 1.5)
        randomCoords(blank_bank_bbox).hover()
        _wait(1, 1.5)
        if BANK_TITLE_BBOX.exists(os.getcwd() + r'\images\bank_title_%s.png' % bank_title, 0.1):
            break
        _wait(2,5)
    else:
        raise RuntimeError("Couldn't open the bank!!!")
    _wait(1,2)
    

def _bank_transaction(withdraw_num=1, dep_all=False, deposit=True):
    '''
    Once in the bank screen
    :param withdraw_num: Number of uniqe items to withdraw
    :param dep_all: click deposit all button or just deposit all items of first inv slot
    :return:
    '''
    assert withdraw_num in (1,2)

    bank_first_item_bbox = BANK_FIRST_ITEM_BBOX
    bank_second_item_bbox = Region(155, 138, 23, 27)
    bank_deposit_all_bbox = Region(536, 786, 31, 26)

    first_inv_bbox = FIRST_INV_BBOX

    # Deposit
    _wait(0.8, 1.3)
    if deposit:
        if dep_all:
            randomCoords(bank_deposit_all_bbox).click()
            _wait(0.8, 1.3)
        else:
            keyDown(Key.SHIFT)
            _wait(0.3, 0.8)
            randomCoords(first_inv_bbox).click()
            _wait(0.5,1)
        
        
    # Withdraw
    if (deposit and dep_all) or not deposit:
        keyDown(Key.SHIFT)
        _wait(0.3, 0.8)
        
    randomCoords(bank_first_item_bbox).click()
    _wait(1, 2)

    if withdraw_num == 2:
        randomCoords(bank_second_item_bbox).click()
        _wait(1, 2)


    keyUp(Key.SHIFT)
    _wait(0.3, 0.8)

    # Close bank
    keyDown(Key.ESC)
    _wait(0.2, 0.4)
    keyUp(Key.ESC)
    _wait(0.7, 1.3)

def _assert_spellbook_selected():
    spellbook_selected_img = os.getcwd() + r'\images\spellbook_selected.png'
    spellbook_selected_red_img = os.getcwd() + r'\images\spellbook_selected_red.png'
    spellbook_selected_bbox = Region(893, 601, 73, 71)

    spellbook_selected_red_pattern = Pattern(spellbook_selected_img)
    spellbook_selected_red_pattern.similar(0.95)
    
    assert (spellbook_selected_bbox.exists(spellbook_selected_red_img, 0.01) or spellbook_selected_bbox.exists(spellbook_selected_red_pattern, 0.01)), 'Spellbook not selected!'

def _alert_low_health_inventory():
    'Read the bars on the inventory screen for health'
    inv_bar_region = Region(664, 901, 22, 18)
    pattern = Pattern(os.getcwd() + r'\images\low_health_inventory.PNG')
    pattern.similar(0.98)
    if not inv_bar_region.exists(pattern, 0.01):
        raise RuntimeError('Low Health!!')
    

def _get_health():
    for _ in range(5):
        t = Region(698, 92, 33, 32).text()
        if t.isnumeric():
            return int(t)
    else:
        raise RuntimeError("Couldn't read health!")
    
def _alert_health(level=20):
    health = _get_health()
    if health <= level:
        for _ in range(5):
            beep(200)
        raise ValueError('Low health!')

def _hide_cursor():
    if not os.path.exists(r'C:\Users\Richard\.runelite\_cursor.png'):
        if not os.path.exists(r'C:\Users\Richard\.runelite\cursor.png'):
            raise AssertionError('Neither form of the cursor image exists!')
        else:
            print('Cursor is already hidden!')
    else:
        os.rename(r'C:\Users\Richard\.runelite\_cursor.png', r'C:\Users\Richard\.runelite\cursor.png')
    
def _show_cursor():
    if not os.path.exists(r'C:\Users\Richard\.runelite\cursor.png'):
        if not os.path.exists(r'C:\Users\Richard\.runelite\_cursor.png'):
            raise AssertionError('Neither form of the cursor image exists!')
        else:
            print('Cursor is already shown!')
    os.rename(r'C:\Users\Richard\.runelite\cursor.png', r'C:\Users\Richard\.runelite\_cursor.png')

def _resetZoom(look_direction=None):
    compass_bbox = Region(744, 45, 30, 25)
    look_direction_dict = {
        'west': Region(628, 36, 316, 253)
    }
    assert look_direction in look_direction_dict or look_direction is None
    
    # Reset zoom and look in a specific cardinal direction
    if look_direction:
        look_bbox = look_direction_dict[look_direction]
        look_Pattern = Pattern(os.getcwd() + r'\images\look_%s.png' % look_direction)
        look_Pattern.similar(0.85)
        for _ in range(3):
            try:
                randomCoords(compass_bbox).rightClick()
                _wait(1,2)
                look_bbox = Region(*fromRaw(look_bbox.find(look_Pattern)))
                break
            except:
                INV_ICON_BBOX.hover()
                _wait(1,2)
        else:
            raise RuntimeError("Couldn't find look direction on compass!!!")
        print('Found direction')
        _wait(0.6, 1)
        randomCoords(look_bbox).click()
    else: # Just reset zoom
        randomCoords(compass_bbox).click()
        
    _wait(0.6, 1)
    keyDown(Key.UP)
    _wait(3,4)
    keyUp(Key.UP)
    _wait(0.6, 1)
    
    keyDown(Key.CTRL)
    _wait(0.6,1)
    keyUp(Key.CTRL)
    _wait(1, 2)

def _zoom(wheel_direction):
    assert wheel_direction in (Button.WHEEL_DOWN, Button.WHEEL_UP)
    mouse_scroll_bbox = Region(61, 157, 456, 389)
    region = randomCoords(mouse_scroll_bbox)
    region.hover()
    for _ in range(random.randint(6, 7)):
        region.wheel(wheel_direction, random.randint(5, 9))
        _wait(0.3, 0.7)

class __KillableThread(threading.Thread):
    def __init__(self, key):
        super(__KillableThread, self).__init__()
        self._kill = threading.Event()
        self.key = key
    
    def run(self):
        while True:
            keyDown(self.key)
            keyUp(self.key)
            # If no kill signal is set, sleep for the interval,
            # If kill signal comes in while sleeping, immediately
            #  wake up and handle
            is_killed = self._kill.wait(0.0)
            if is_killed:
                break
        
        print("Killing Thread")
    
    def kill(self):
        self._kill.set()


class press_and_hold_key(object):
    def __init__(self, key):
        self.key = key
        self.thread = __KillableThread(self.key)
    
    def __enter__(self):
        self.thread.start()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.thread.kill()
        self.thread.join(0.0)
        
class MaxTimeError(Exception):
    def __init__(self):
        super(Exception, self).__init__('Past max time')
        
class LevelUpError(Exception):
    def __init__(self):
        super(Exception, self).__init__('level up message')

def fromRaw(rawRegion):
    return [rawRegion.getX(), rawRegion.getY(), rawRegion.getW(), rawRegion.getH()]

def _wait(a, b):
    sleepTime = random.uniform(float(a), float(b))
    time.sleep(sleepTime)
    return sleepTime
        
def randomCoords(coords):
    if isinstance(coords, Region):
        coords = fromRaw(coords)
    newX = coords[0] + random.randrange(0, coords[2])
    newY = coords[1] + random.randrange(0, coords[3])
    return Region(newX, newY, 0, 0)

def beep(wait):
    '''
    :param wait(ms):
    :return:
    '''
    java.awt.Toolkit.getDefaultToolkit().beep()
    time.sleep(wait / float(1000))
    
def _checkLevelUp():
    levelupRegion = Region(504, 837, 141, 60)
    levelupImage = Pattern(os.getcwd() + r'\images\levelup.png')
    levelupImage.similar(0.95)
    if levelupRegion.exists(levelupImage, 0.01):
        randomCoords(levelupRegion).click()
        _wait(0.2,0.5)
        for _ in range(5):
            _wait(0.5, 0.7)
            keyDown(Key.SPACE)
            _wait(0.1, 0.3)
            keyUp(Key.SPACE)
            if not levelupRegion.exists(levelupImage):
                break
        raise LevelUpError()

def waitFor(region, image, numTries=None, maxTime=None, inverse=False):
    '''
    Waits for an image
    :param region:
    :param image:
    :param numTries: int, max number of attempts. Raises StopIteration
    :param maxTime: datetime.datetime or datetime.timedelta. Raises
    :return:
    '''
    image = os.getcwd() + (r'\images\%s' % image ) + '.png' if not image.endswith('.png') else ''
    assert os.path.exists(image)
    
    iter=0
    if numTries:
        assert isinstance(numTries, int)
    if maxTime:
        assert isinstance(maxTime, (datetime.datetime, datetime.timedelta))
        if isinstance(maxTime, datetime.timedelta):
            maxTime = datetime.datetime.now() + maxTime
    opr = operator.truth if not inverse else operator.not_
    while not opr(region.exists(image, 0.2)):
        if numTries:
            iter += 1
            if iter == numTries:
                raise StopIteration('hit max attempts')
        if maxTime:
            if datetime.datetime.now() >= maxTime:
                raise MaxTimeError()
        _checkLevelUp()


OBSERVED_EVENT = False
def waitForChange(region, maxTime):
    """
    Wait until ANY changes are observed in a region.
    Raises RuntimeError if none are observed
    :param region:
    :param maxTime:
    :return:
    """
    global OBSERVED_EVENT
    OBSERVED_EVENT = False
    
    region = Region(*fromRaw(region))

    def changeHandler(event):
        global OBSERVED_EVENT
        OBSERVED_EVENT = True
        event.region.stopObserver()

        
    region.onChange(50, changeHandler)
    region.observe(maxTime, background=False)
    region.stopObserver()
    if not OBSERVED_EVENT:
        raise RuntimeError("Didn't observe any changes in given region.")
        

def mining():
    '''
    Set to half window (left), center viewing angle, zoom all the way in, minimize chat.
    Allow custom cursors
    Orient such that ore is left
    '''
    
    print('Go to the Mining Guild!!!!!')
    
    ore_bbox_W = Region(206, 508, 101, 87)
    ore_bbox_E = Region(600, 496, 113, 102)
    ore_bbox_S = Region(410, 702, 107, 106)
    
    inventory_slot_bbox = FIRST_INV_BBOX

    randomCoords(INV_ICON_BBOX).click()
    
    #TODO
    _hide_cursor()
    
    _wait(0.4, 0.7)
    keyDown(Key.SHIFT)
    _wait(0.4, 0.7)

    try:
        # Time to mine ore
        while True:
            # Timeout
            #if datetime.datetime.now() > datetime.datetime(2020,11,20,4):
            #    return
            for ore_bbox in [ore_bbox_W, ore_bbox_S, ore_bbox_E]:
                _assert_player_in_tile()
                
                randomCoords(ore_bbox).click()
                _wait(0.1, 0.3)
                
                inv_bbox = randomCoords(inventory_slot_bbox)

                inv_bbox.hover()
                
                try:
                    waitFor(inventory_slot_bbox, 'empty_inventory', maxTime=datetime.timedelta(seconds=3), inverse=True)
                except MaxTimeError:
                    continue
                except LevelUpError:
                    continue
                
                _wait(0.1, 0.2)
                inv_bbox.click()
                _wait(0.1, 0.3)
                
                
        
                #if ore_bbox.exists(os.getcwd() + r'\images\iron_rock_color.png' , 0.2):
                #    continue
                #else:
                #    _wait(0.5, 0.7)
    finally:
        keyUp(Key.SHIFT)


def _agility(info):
    print('Make sure the side panels are minimized in options!')
    # info = (
    #   Outer region of the click box,
    #   Inner region of the click box (What to click on),
    #   Bbox of the roof(where to search for marks of grace)
    #   Time to wait for animation to complete,
    # )
    raw_input('Press enter when ready...')
    
    maxTime = 5 + max([x[-1] for x in info])
    graceIndex = None
    
    center_bbox = Region(463, 509, 45, 45)
    
    entire_screen_bbox = Region(9, 237, 940, 700)
    
    def checkRedAgility(reg):
        if reg.exists(os.getcwd() + r'\images\agility_red.png', 0.01):
            for _ in range(5):
                beep(500)
            raise RuntimeError('Mark of grace!')
        
    while True:
        for index, (outerRegion, clickRegion, roofRegion, sleeptime) in enumerate(info):
            if center_bbox.exists(os.getcwd() + r'\images\agility_player_fell_down.png', 0.01):
                _zoom(Button.WHEEL_UP)
                try:
                    _assert_player_in_tile()
                except AssertionError:
                    print('What?')
                    _zoom(Button.WHEEL_DOWN)
                    raise RuntimeError('Player fell down!')
            
            if graceIndex == index:
                raise RuntimeError('Mark of grace was found, but was not picked up!')
            
            if outerRegion.exists(os.getcwd() + r'\images\agility_red.png', 0.01):
                graceIndex = index
                
                
            if roofRegion and roofRegion.exists(os.getcwd() + r'\images\mark_of_grace.png', 0.01):
                for _ in range(5):
                    beep(500)
                raw_input('Collect mark and goto the next one, then press enter')
                graceIndex = None
                continue
                    
            img = 'agility_red' if isinstance(graceIndex, int) else 'agility_green'
            waitFor(outerRegion, img, maxTime=datetime.timedelta(seconds=maxTime))
            
            _wait(0.8, 1.5)

            randomCoords(clickRegion).click()

            slept_time = _wait(sleeptime, sleeptime+0.5)
            _wait(0.8, 1.5)
            print('Waited for %f for %d' % (slept_time, index,))
    

def agility_canifis():
    'Start after the first one'
    info = [
        (Region(425, 318, 92, 110), Region(448, 354, 44, 39), Region(404, 352, 235, 229), 5),
        (Region(311, 495, 54, 78), Region(322, 508, 28, 52), Region(303, 427, 255, 159), 4.6),
        (Region(286, 626, 46, 78), Region(297, 638, 22, 54), Region(280, 478, 248, 226), 4.9),
        (Region(431, 690, 41, 78), Region(441, 701, 20, 54), Region(325, 480, 200, 274), 5),
        (Region(498, 574, 68, 75), Region(520, 600, 20, 22), Region(428, 480, 222, 206), 7),
        #Region(851, 518, 28, 41)  Region(887, 518, 28, 41)
        (Region(828, 497, 67, 79), Region(856, 518, 18, 41), Region(433, 434, 461, 342), 6.5),
        (Region(458, 314, 43, 66), Region(470, 330, 19, 37), Region(395, 322, 263, 293), 5),
        (Region(271, 380, 196, 76), Region(319, 394, 63, 16), None, 7.5),  # Marks of grace should never appear here.
    ]
    _agility(info)

def dartSmithing():
    
    'start next to southern most bank, full inventory, bank tab preset'
    
    
    bank_bbox = Region(420, 210, 18, 19)
    
    anvil_bbox = Region(559, 834, 7, 10)
    dart_bbox = Region(431, 276, 37, 39)
    bank_title_bbox = BANK_TITLE_BBOX
    
    bars = int(raw_input('Number of iron bars: '))
    numRuns = int(math.ceil(bars / 27.0))
    print('numRuns = %d' % numRuns)
    for _ in range(numRuns):
        randomCoords(anvil_bbox).click()
        _wait(6.8, 7.5)
        
        randomCoords(dart_bbox).click()
        _wait(80,90)
        
        
        randomCoords(bank_bbox).click()
        try:
            waitFor(bank_title_bbox, 'bank_title_darts', maxTime=datetime.timedelta(seconds=10))
        except:
            java.awt.Toolkit.getDefaultToolkit().beep()
            raise
        
        _wait(1,3)
        _bank_transaction(deposit=False)


def camelotTele():
    numTele = int(raw_input('Number of teleports: '))
    
    tele_bbox = Region(859, 757, 25, 22)
    
    clickRegion = randomCoords(tele_bbox)
    
    for i in range(numTele):
        print(numTele-i-1)
        _assert_spellbook_selected()
        if not random.randint(0, 20):
            clickRegion = randomCoords(tele_bbox)
        clickRegion.click()
        _wait(3.3, 3.8)

def highAlch():
    numAlch = int(raw_input('Number of items: '))
    
    alch_bbox = Region(895, 789, 9, 9)
    
    clickRegion = randomCoords(alch_bbox)
    
    for i in range(numAlch):
        print(numAlch - i - 1)
        _assert_spellbook_selected()
        if not random.randint(0, 50):
            clickRegion = randomCoords(alch_bbox)
        clickRegion.click()
        _wait(0.3, 0.7)
        clickRegion.click()
        _wait(2.3, 3.0)

def firemaking():
    '''
    Inventory layout:
        Tinderbox: top left
        Junk: rest of top row
        Junk: 2nd from the bottom row, left most column.
        Junk: bottom most row, all but left most column.
        Noted logs: bottom right
    Start with only these two items.
    Start at the grand exchange, with player models off, directly west of the top left banker, zoomed all the way IN.
    '''
    numLogs = int(raw_input('Number of logs: '))
    
    logs_per_run = 19
    numRuns = int(math.ceil(numLogs / float(logs_per_run)))
    
    noted_logs_bbox = LAST_INV_BBOX
    tinderbox_bbox = Region(714, 678, 30, 30)
    bank_outer_bbox = Region(576, 467, 170, 143)
    bank_bbox = Region(666, 516, 80, 70)
    step_left_bbox = Region(246, 507, 134, 90)

    step_down_left_bbox = Region(231, 628, 139, 128)
    
    banker_foot = Pattern(os.getcwd() + r'\images\banker_foot.png')
    banker_foot.similar(0.80)
    
    initial_item_bbox = [711, 723, 34, 31]
    item_bbox_X_translate = 53
    item_bbox_Y_translate = 46
    
    # Arbitrary region on the screen, used to monitor for movement that occurs when a fire is
    #   successfully started, signalling that a new fire can be attempted.
    started_fire_observer_bboxs = (Region(51, 178, 212, 173), Region(46, 691, 184, 176))

    bank_return_pos_bbox = Region(930, 530, 16, 16)
    bankstand_marker_bboxs = ( Region(18, 53, 717, 921), Region(683, 249, 268, 362))

    ground_marker = Pattern(os.getcwd() + r'\images\firemaking_bank_ground_marker.png')
    ground_marker.similar(0.80)
    centered_bankstand_bbox = Region(379, 439, 95, 111)
    
    allowed_misobservations = 1

    #TODO fill the unused inventory slots with misc garbage to prvent miscounting.
    for numRun in range(numRuns):
        misobservations = 0
        start_time = time.time()
        # Make sure the banker is where it should be
        assert bank_outer_bbox.exists(banker_foot)
        
        # Un-note the logs and step left to a vaild firemaking spot.
        randomCoords(noted_logs_bbox).click()
        _wait(0.2, 0.5)
        randomCoords(bank_bbox).click()
        _wait(1, 2)
        keyDown('1')
        _wait(0.1, 0.3)
        keyUp('1')
        _wait(1,2)
        if numRun % 2:
            randomCoords(step_down_left_bbox).click()
        else:
            randomCoords(step_left_bbox).click()
        _wait(1.5,2.5)

        
        # Start burning the logs
        for rowNum in range(5):
            for colNum in range(4):
                if rowNum == 4 and colNum == 3:
                    #Last row only has 3 items.
                    break
                randomCoords(tinderbox_bbox).click()
                _wait(0.3, 0.5)
                
                item_bbox = Region(
                    initial_item_bbox[0] + (item_bbox_X_translate * colNum),
                    initial_item_bbox[1] + (item_bbox_Y_translate * rowNum),
                    27,
                    24
                )
                
                randomCoords(item_bbox).click()
                try:
                    waitForChange(started_fire_observer_bboxs[numRun % 2], 7)
                except RuntimeError:
                    if misobservations > allowed_misobservations:
                        raise
                    misobservations += 1
                    continue
                _wait(0.3, 0.5)
        _wait(0.3,0.5)
                
        # Run back to the banker to repeat the process
        _zoom(Button.WHEEL_DOWN)
        randomCoords(bank_return_pos_bbox).click()
        _wait(9, 11)
        _zoom(Button.WHEEL_UP)
        _wait(1,3)
        
        for marker_bbox in bankstand_marker_bboxs:
            if marker_bbox.exists(ground_marker, 0.01):
                bankstand = marker_bbox.find(ground_marker)
                bankstand = fromRaw(bankstand)
                bankstand[0] += 10
                randomCoords(bankstand).click()
                _wait(3, 5)
                bank_bbox.hover()
                break
        else:
            raise RuntimeError("Couldn't find bankstand marker! Did you remember to mark it?")
        assert bank_outer_bbox.exists(banker_foot) or Region(379, 439, 95, 111).exists(ground_marker, 1)


        _wait(0.9, 1.2)
        
        #timeToWait = abs(120 - int(time.time() - start_time) + 1)
        #print('Completed a set, waiting %d seconds for fires to die before starting the next one.' % timeToWait)
        #_wait(timeToWait, timeToWait+10)
    beep(500)
    
def glassBlowing():
    bank_bbox = Region(633, 478, 73, 65)
    numGlass = int(raw_input('Number of molten glass: '))

    glass_per_run = 26
    numRuns = int(math.ceil(numGlass / float(glass_per_run)))

    noted_glass_bbox = LAST_INV_BBOX
    pipe_bbox = Region(714, 678, 30, 30)
    first_glass_bbox = Region(767, 686, 23, 21)
    
    for _ in range(numRuns):
        # Un-note the glass
        randomCoords(noted_glass_bbox).click()
        _wait(0.2, 0.5)
        randomCoords(bank_bbox).click()
        _wait(1, 2)
        keyDown('1')
        _wait(0.1, 0.3)
        keyUp('1')
        _wait(1, 2)
        
        # Start the process
        randomCoords(pipe_bbox).click()
        _wait(0.2,0.7)
        randomCoords(first_glass_bbox).click()
        _wait(1, 2)

        keyDown('6')
        _wait(0.1, 0.3)
        keyUp('6')
        _wait(1, 2)
        
        waitTime = 1.8*glass_per_run
        
        _wait(waitTime+ 3, waitTime + 7)

        randomCoords(bank_bbox).click()
        _wait(0.7, 1.3)
        keyDown(Key.SHIFT)
        _wait(0.1, 0.3)
        randomCoords(first_glass_bbox).click()
        _wait(0.1, 0.2)
        keyUp(Key.SHIFT)
        _wait(0.7, 1.3)

        keyDown(Key.ESC)
        _wait(0.1, 0.3)
        keyUp(Key.ESC)
        _wait(0.7, 1.3)
        
def _dump_inventory(exclude_slots=[]):
    '''
    Will dump the entire inventory on the ground except for the bottom row.
    :param exclude_slots: list of 2 tuple of inventory slot coordinates to exclude from dumping.
        Ex) To prevent top right, use (3, 0).
        Ex) To prevent bottom left (remember the last row is always excluded), use (5, 0).
    :return: Number of items dumped.
    '''
    print('Dumping Inventory')
    
    for excluded_slot in exclude_slots:
        assert isinstance(excluded_slot, tuple) and len(excluded_slot) == 2
        assert 0 < excluded_slot[0] <= 3
        assert 0 < excluded_slot[1] <= 5 #skip the last row
    
    inventory_icon_bbox = INV_ICON_BBOX
    mouse_move_region = Region(101, 156, 359, 205)
    first_inv_bbox = [714, 678, 30, 30]
    item_bbox_X_translate = 53
    item_bbox_Y_translate = 46
    randomCoords(mouse_move_region).hover()
    
    # Find items to dump
    inv_slots_to_dump = []
    for rowNum in range(6):  # Keep contents bottom row
        colIter = range(4) if not rowNum % 2 else reversed(range(4))  # Make it an S pattern
        for colNum in colIter:
            if (colNum, rowNum) in exclude_slots:
                continue
            inventory_slot_bbox = Region(
                first_inv_bbox[0] + (item_bbox_X_translate * colNum),
                first_inv_bbox[1] + (item_bbox_Y_translate * rowNum),
                30,  # 27
                30  # 24
            )
            if not inventory_slot_bbox.exists(os.getcwd() + r'\images\woodcutting_empty_inventory_slot.png', 0):
                inv_slots_to_dump.append(inventory_slot_bbox)
    _wait(1, 2)
    
    
    # Dump items
    keyDown(Key.SHIFT)
    _wait(0.8, 1.2)
    for region in inv_slots_to_dump:
        randomCoords(region).click()
        _wait(0.3, 0.6)

    keyUp(Key.SHIFT)
    _wait(1, 2)
    return len(inv_slots_to_dump)
        
def woodcutting():
    '''
    Camera up, zoomed all the way in, tree on the right.
    :return:
    '''
    tree_bbox = Region(665, 487, 120, 99)
    inventory_icon_bbox = INV_ICON_BBOX
    mouse_move_region = Region(101, 156, 359, 205)
    while True:
        randomCoords(tree_bbox).click()
        _wait(1,2)
        randomCoords(mouse_move_region).hover()
        waitFor(tree_bbox, 'woodcutting_yellow_timer', maxTime=datetime.timedelta(seconds=200))
        _wait(1, 5)
        _dump_inventory()
        
        waitFor(tree_bbox, 'woodcutting_yellow_timer',maxTime=datetime.timedelta(seconds=10), inverse=True)
        print('Tree is back')
        _wait(1,5)
        

def humidifyClay():

    numClay = int(raw_input('Clay: '))
    numRuns = int(math.floor(numClay / 27.0))
    print('Will need %d Astral Runes.' % numRuns)
    
    humidify_bbox = Region(796, 700, 24, 20)
    
    for i in range(numRuns):
        print(numRuns - i - 1)
        _assert_spellbook_selected()
        _assert_standing_at_bank()
        randomCoords(humidify_bbox).click()
        _wait(2.5,4)
        
        _ge_click_banker('clay')
        _bank_transaction()

def tanLeather():
    numHides = int(raw_input('Hides: '))
    numRuns = int(math.floor(numHides / 25.0))
    print('Will need %d Astral Runes.' % (numRuns*2*5))
    print('Will need %d Nature Runes.' % (numRuns*5))
    tan_bbox = Region(751, 805, 14, 18)
    
    for i in range(numRuns):
        print(numRuns - i - 1)
        _assert_spellbook_selected()
        _assert_standing_at_bank()
        for _ in range(5):
            randomCoords(tan_bbox).click()
            _wait(2, 2.5)
        
        _ge_click_banker('tan')
        _bank_transaction()
        _wait(1,2)


def _fishing(fish):
    '''
    Zoomed in
    Vertical camera
    Hide all entities EXCEPT NPCs
    Have fishing spots oriented to be above you (relative North).
        Can do exact movements by right clicking on compass.
    Hide minimap
    :return:
    '''
    print('Make sure to hide all entities EXCEPT for NPCs')

    player_region = Region(-1528, 441, 148, 138)
    
    total_fish_area_bbox = Region(-1910, 247, 925, 127)
    
    last_inv_slot = LAST_INV_BBOX
    
    mouse_move_region = Region(-1784, 671, 324, 256)
    
    # Constant. Will always be the north tile
    current_fish_region = Region(-1518, 259, 199, 106)

    empty_inv_slot_img = os.getcwd() + r'\images\woodcutting_empty_inventory_slot.png'
    fish_img = os.getcwd() + r'\images\fishing\%s.png' % fish
    
    MAX_FISH_FIND_ATTEMPTS = 3
    
    fish_areas = []
    fish_bbox = None
    
    def find_closest_spot(fish_areas):
        player_center = player_region.center
        player_coords = (player_center.getX(), player_center.getY())
        closest_distance = 100000
        closest = None
        for area in fish_areas:
            center = area.center
            coords = (center.getX(), center.getY())
            distance = math.sqrt( math.pow((player_coords[0] - coords[0]), 2) + math.pow((player_coords[1] - coords[1]), 2) )
            if distance < closest_distance:
                closest = area
        return closest
        
    
    
    while True:
        if not fish_bbox or not fish_bbox.exists(fish_img, 0.01):
            for _ in range(MAX_FISH_FIND_ATTEMPTS):
                try:
                    print('Attempting to find fishing spot.')
                    fish_areas = total_fish_area_bbox.findAll(fish_img)
                    break
                except FindFailed:
                    _wait(15, 30)
            else:
                raise RuntimeError("Couldn't find a fishing spot!")
            
            print('Found fishing spots')
            
            fish_bbox = fromRaw(find_closest_spot(fish_areas))
            fish_bbox = Region(
                fish_bbox[0] - 15,
                fish_bbox[1] - 15,
                fish_bbox[2] + 15,
                fish_bbox[3] + 15
            )
            print('Found closest fishing spot')
        else:
            print('Using old fishing spot')
            
        _wait(1,3)
        randomCoords(fish_bbox).click()
        _wait(1,3)
        randomCoords(mouse_move_region).hover()
        _wait(3,6)

    

        maxTime = time.time() + 200
        try:
            while True:
                # If last inventory slot is full
                if not last_inv_slot.exists(empty_inv_slot_img, 0.2):
                    break
                if not current_fish_region.exists(fish_img, 0.2):
                    time.sleep(1)
                    if not current_fish_region.exists(fish_img, 0.2):
                        raise ValueError('Fishing spot depleted')
                if time.time() >= maxTime:
                    raise MaxTimeError()
                _checkLevelUp()
        except Exception as e:
            print(e)
        
        _wait(2,4)
        _dump_inventory()
        _wait(1,3)
            
        
    
    
def salmon():
    _fishing('salmon')
    
    
def cooking():
    '''
    Cooking karambwan at Hosidious
    Zoom all the way in
    Vertical camera
    Looking south
    :return:
    '''
    numFish = int(raw_input('Number of Karambwan: '))
    numRuns = int(math.floor(numFish / 28.0))
    
    
    inventory_icon_bbox = INV_ICON_BBOX
    oven_outer_bbox = Region(-1595, 650, 266, 234)
    oven_bbox = Region(-1507, 723, 96, 95)

    last_inv_slot = Region(-1050, 948, 30, 30)
    bank_bbox = Region(-1399, 371, 16, 15)
    bank_title_bbox = BANK_TITLE_BBOX
    oven_stand_bbox = Region(-1495, 652, 14, 16)
    
    
        
        
    randomCoords(inventory_icon_bbox).click()
    _wait(0.5, 1)
    for numIter in range(numRuns):
        assert oven_outer_bbox.exists(os.getcwd() + r'\images\cooking_oven.png', 0.01)
        
        with press_and_hold_key('2'):
            _wait(0.4, 0.6)
            random_last_inv_slot_bbox = randomCoords(last_inv_slot)
            for _ in range(28):
                if not last_inv_slot.exists(os.getcwd() + r'\images\raw_karambwan.png', 0.01):
                    break
                random_last_inv_slot_bbox.click()
                _wait(0.0, 0.15)
                randomCoords(oven_bbox).click()
                t1 = time.time()
                _wait(0.2, 0.4)
                random_last_inv_slot_bbox = randomCoords(last_inv_slot)
                random_last_inv_slot_bbox.hover()
                waitTime = max(0.4 - (time.time()-t1), 0)
                _wait(waitTime, waitTime+0.2)

        print('Cooked all')
            
        _wait(0.3, 0.9)
        _zoom(Button.WHEEL_DOWN)
        _wait(0.3, 0.9)
        randomCoords(bank_bbox).click()
        waitFor(bank_title_bbox, 'cooking', maxTime=datetime.timedelta(seconds=15))
        _wait(1, 1.5)
        
        _bank_transaction(dep_all=True)
        
        randomCoords(oven_stand_bbox).click()
        _wait(3.2, 3.7)
        _zoom(Button.WHEEL_UP)
        _wait(0.5, 1)
        
        
def barbarian_fishing():
    '''
        Zoomed in
        Vertical camera
        Hide all entities EXCEPT NPCs
        Have fishing spots oriented to be above you (relative North).
            Can do exact movements by right clicking on compass.
        Hide minimap
        Turn off Ground Items
        :return:
        '''
    print('Make sure to hide all entities EXCEPT for NPCs')
    
    player_region = Region(-1528, 441, 148, 138)
    zoomed_player_region = Region(-1443, 521, 15, 15)
    
    total_fish_area_bbox = Region(-1910, 247, 925, 127)
    
    zoomed_total_fish_area_bbox = Region(-1694, 466, 683, 58)
    
    first_inv_slot = Region(-1206, 678, 30, 30)
    
    mouse_move_region = Region(-1209, 444, 214, 151)
    
    # Constant. Will always be the north tile
    current_fish_region = Region(-1518, 259, 199, 106)
    
    empty_inv_slot_img = os.getcwd() + r'\images\woodcutting_empty_inventory_slot.png'
    fish_img = os.getcwd() + r'\images\fishing\barbarian.png'
    
    MAX_FISH_FIND_ATTEMPTS = 3
    
    fish_areas = []
    fish_bbox = None
    
    
    def find_closest_spot(player_loc, fish_areas):
        player_center = player_loc.center
        player_coords = (player_center.getX(), player_center.getY())
        closest_distance = 100000
        closest = None
        for area in fish_areas:
            center = area.center
            coords = (center.getX(), center.getY())
            distance = math.sqrt(
                math.pow((player_coords[0] - coords[0]), 2) + math.pow((player_coords[1] - coords[1]), 2))
            if distance < closest_distance:
                closest = area
        return closest
    
    def findFish():
        for _ in range(MAX_FISH_FIND_ATTEMPTS):
            try:
                print('Attempting to find fishing spot.')
                fish_areas = total_fish_area_bbox.findAll(fish_img)
                break
            except FindFailed:
                _wait(15, 30)
        else:
            raise RuntimeError("Couldn't find a fishing spot!")
        print('Found fishing spots')

        fish_bbox = fromRaw(find_closest_spot(player_region, fish_areas))
        fish_bbox = Region(
            fish_bbox[0] - 15,
            fish_bbox[1] - 15,
            fish_bbox[2] + 15,
            fish_bbox[3] + 15
        )
        print('Found closest fishing spot')
        return fish_bbox
        
    while True:
        if not fish_bbox or not fish_bbox.exists(fish_img, 0.01):
            if total_fish_area_bbox.exists(fish_img, 0.01):
                fish_bbox = findFish()
            else:
                raise RuntimeError
                _zoom(Button.WHEEL_DOWN)
                if not zoomed_total_fish_area_bbox.exists(os.getcwd() + r'\images\fishing\barbarian_zoom_edge.png', 0.01):
                    raise RuntimeError("Couldn't find regardless of zoom level")
                else:
                    fish_zoom_areas = zoomed_total_fish_area_bbox.findAll(os.getcwd() + r'\images\fishing\barbarian_zoom_edge.png')
                    closest_zoom = fromRaw(find_closest_spot(zoomed_player_region, fish_zoom_areas))
                    closest_zoom = Region(
                        closest_zoom[0] - 15,
                        closest_zoom[1] - 15,
                        closest_zoom[2] + 15,
                        closest_zoom[3] + 15
                    )
                    randomCoords(closest_zoom).click()
                    _wait(3,5)
                    _zoom(Button.WHEEL_UP)
                    fish_bbox = findFish()
                
            
            
        else:
            print('Using old fishing spot')
        
        randomCoords(fish_bbox).click()
        _wait(0.5, 1)
        randomCoords(mouse_move_region).hover()
        _wait(0.5, 1)
        
        
        
        maxTime = time.time() + 20
        try:
            while True:
                # If last inventory slot is full
                if not first_inv_slot.exists(empty_inv_slot_img, 0.01):
                    break
                if not fish_bbox.exists(fish_img, 0.01):
                    time.sleep(1)
                    if not fish_bbox.exists(fish_img, 0.2):
                        raise ValueError('Fishing spot depleted')
                if time.time() >= maxTime:
                    raise MaxTimeError()
                _checkLevelUp()
        except Exception as e:
            print(e)

        _wait(0.1, 0.3)
        keyDown(Key.SHIFT)
        _wait(0.1, 0.3)
        
        randomCoords(first_inv_slot).click()
        _wait(0.1, 0.3)

        keyUp(Key.SHIFT)
        _wait(0.1, 0.3)
        
def _mixPotions(use):
    numPots = int(raw_input('Number of potions: '))
    numRuns = int(math.floor(numPots / 14.0))
    
    inv_mix_slot_1 = Region(771, 817, 20, 21)
    inv_mix_slot_2 = Region(822, 820, 21, 26)
    
    last_inv_bbox = LAST_INV_BBOX
    
    for i in range(numRuns):
        print(numRuns - i - 1)

        _assert_standing_at_bank()

        randomCoords(inv_mix_slot_1).click()
        _wait(0.1,0.3)
        randomCoords(inv_mix_slot_2).click()
        
        _wait(1, 1.5)
        keyDown(Key.SPACE)
        _wait(0.3, 0.6)
        keyUp(Key.SPACE)
        _wait(2, 3)
        try:
            waitFor(last_inv_bbox, 'woodcutting_empty_inventory_slot', maxTime=datetime.timedelta(seconds=1.2*16))
        except LevelUpError:
            pass
        _wait(0.6, 1)

        _ge_click_banker(use)

        _bank_transaction(withdraw_num=2, dep_all=True)
    
def herblore():
    _mixPotions('herblore')

def fruitStall():
    inventory_icon_bbox = INV_ICON_BBOX
    stall_bbox = Region(634, 501, 141, 108)
    first_inv_bbox = FIRST_INV_BBOX
    
    #with press_and_hold_key()
    randomCoords(inventory_icon_bbox).click()
    keyDown(Key.SHIFT)
    _wait(0.3, 0.5)
    try:
        while True:
            randomCoords(stall_bbox).click()
            try:
                waitFor(first_inv_bbox, 'woodcutting_empty_inventory_slot', maxTime=datetime.timedelta(seconds=3), inverse=True)
            except Exception:
                continue
            _wait(0.2, 0.5)
            randomCoords(first_inv_bbox).click()
            _wait(0.9, 1.2)
    finally:
        keyUp(Key.SHIFT)


def ensouledHeads():
    '''
    Camera verticle.
    Hide everything in entity hider
    Zoomed out
    :return:
    '''
    headType = raw_input('Head type: ').lower()
    spellbook_locations = {
        'dag': Region(708, 874, 18, 18),
        'kal': Region(826, 837, 22, 26),
    }

    spellbook_bbox = spellbook_locations[headType]

    look_bbox = Region(3, 210, 752, 486)
    
    item_bbox_X_translate = 53
    item_bbox_Y_translate = 46
    initial_item_bbox = fromRaw(FIRST_INV_BBOX)
    initial_item_bbox[1] += item_bbox_Y_translate
    
    for row in range(6):
        for col in range(4):
            try:
                #try:
                #    _alert_health()
                #except RuntimeError:
                #    pass

                _assert_spellbook_selected()
                randomCoords(spellbook_bbox).click()
                _wait(0.3, 0.8)

                item_bbox = Region(
                    initial_item_bbox[0] + (item_bbox_X_translate * col),
                    initial_item_bbox[1] + (item_bbox_Y_translate * row),
                    27,
                    24
                )

                randomCoords(item_bbox).click()

                # Wait for it to appear
                waitFor(look_bbox, 'ensouled_head', maxTime=datetime.timedelta(seconds=15))
                print('head appeared')
                # Wait for it to die
                waitFor(look_bbox, 'ensouled_head', inverse=True)

                _wait(1, 2)
            except LevelUpError:
                pass
          

def fletching():
    numLogs = int(raw_input('Num logs: '))
    pressDown = str(int(raw_input('Key to press down in option menu: ')))
    
    numRuns = int(math.ceil(numLogs / 27.0))

    first_inv_bbox = FIRST_INV_BBOX

    for i in range(numRuns):
        print(numRuns - i - 1)
        _ge_click_banker('fletching')
        _bank_transaction()
    
        # Knife to logs
        randomCoords(LAST_INV_BBOX).click()
        _wait(0.6, 1)
        randomCoords(first_inv_bbox).click()
        _wait(0.6, 1)

        # Make selection
        _wait(1, 2)
        keyDown(pressDown)
        _wait(0.1, 0.3)
        keyUp(pressDown)
        _wait(1,2)
        
        _wait(50,55)
    
def knight_pickpocket():
    '''
    Put coins in last inventory slot
    Mouse tooltips off
    World 378 or 302
    :return:
    '''
    
    print('Try world 378 or 302')
    
    raw_input('Is NPC attack options off? ')
    
    entire_screen_bbox = Region(2, 33, 939, 956)

    knight_click_tile = None
    NW, SW = None, None

    NW_pattern = Pattern(os.getcwd() + r'\images\pickpocket_NW_corner.png')
    NW_pattern.similar(0.95)
    SE_pattern = Pattern(os.getcwd() + r'\images\pickpocket_SE_corner.png')
    SE_pattern.similar(0.95)

    bank_pattern = Pattern(os.getcwd() + r'\images\knight_pickpocket_bank_booth.png')
    bank_pattern.similar(0.5)

    bank_title_bbox = BANK_TITLE_BBOX
    blank_bank_bbox = Region(158, 284, 344, 354)
    
    # For healing
    def get_heal_bboxes():
        item_bbox_X_translate = 53
        item_bbox_Y_translate = 46
        inv_bboxes = []
        for row in range(6):
            row += 1
            colIter = range(4) if not row % 2 else reversed(range(4))
            for col in colIter:
                tmp_bbox = fromRaw(FIRST_INV_BBOX)
                tmp_bbox[0] += item_bbox_X_translate*col
                tmp_bbox[1] += item_bbox_Y_translate*row
                inv_bboxes.append(Region(*tmp_bbox))
        return inv_bboxes
    inv_bboxes = get_heal_bboxes()

    _resetZoom('west')

    while True:
        for _ in range(28):
            try:
                _alert_low_health_inventory()
            except RuntimeError:
                # Heal
                _wait(0.6, 1)
                if len(inv_bboxes) == 0:
                    _zoom(Button.WHEEL_DOWN)
                    _wait(1,2)
                    bank_bbox = fromRaw(entire_screen_bbox.find(bank_pattern))
                    randomCoords(bank_bbox).click()
                    waitFor(bank_title_bbox, 'bank_title_pickpocket', maxTime=datetime.timedelta(seconds=15))
                    _wait(1,2)
                    
                    keyDown(Key.SHIFT)
                    _wait(0.5,1)
                    randomCoords(LAST_INV_BBOX).click()
                    _wait(1,1.5)

                    randomCoords(BANK_FIRST_ITEM_BBOX).click()
                    _wait(0.5, 1)
            
                    keyUp(Key.SHIFT)
                    _wait(0.3, 0.7)

                    randomCoords(FIRST_INV_BBOX).click()
                    _wait(1,2)

                    keyDown(Key.ESC)
                    _wait(0.1, 0.3)
                    keyUp(Key.ESC)
                    _wait(0.7, 1.3)

                    _resetZoom('west')
                    
                    inv_bboxes = get_heal_bboxes()
                    
                for _ in range(4):
                    inv_food_bbox = inv_bboxes.pop()
                    randomCoords(inv_food_bbox).click()
                    _wait(1.8, 2.3)
                #beep(100)
                #raw_input('Heal and press enter to continue: ')
            
            knight_moved_wait = False
            
            # If knight moved
            if NW and (not Region(*fromRaw(NW)).exists(NW_pattern, 0.01) or not Region(*fromRaw(SE)).exists(SE_pattern, 0.01)):
                knight_click_tile = None

            # Get where to click
            if knight_click_tile is None:

                NW = entire_screen_bbox.find(NW_pattern)
                SE = entire_screen_bbox.find(SE_pattern)
                
                NWc = NW.center
                SEc = SE.center
                
                x_offset = 25
                y_offset = 32
                
                knight_region = Region(NWc.getX() + x_offset, NWc.getY() + y_offset, SEc.getX() - NWc.getX() - (2*x_offset), SEc.getY() - NWc.getY() - (2*y_offset))

                knight_click_tile = randomCoords(knight_region)

                knight_moved_wait = True

            knight_click_tile.click()
            
            _wait(0.8, 1.3)
            
            if knight_moved_wait:
                _wait(1,2)
            
            
        
        _wait(1,2)
        randomCoords(FIRST_INV_BBOX).click()
        knight_click_tile = None
        _wait(1,2)


def crafting():
    numLeather = int(raw_input('Num items: '))
    pressDown = str(int(raw_input('Key to press down in option menu: ')))
    
    numRuns = int(math.floor(numLeather / 24.0))
    
    needle_bbox = LAST_INV_BBOX
    
    leather_bbox = fromRaw(LAST_INV_BBOX)
    leather_bbox[1] -= 46
    leather_bbox = Region(*leather_bbox)
    
    for i in range(numRuns):
        print(numRuns - i - 1)
        _ge_click_banker('crafting')
        _bank_transaction()
        
        # Knife to logs
        randomCoords(needle_bbox).click()
        _wait(1, 2)
        randomCoords(leather_bbox).click()
        _wait(1, 2)
        
        # Make selection
        _wait(1, 2)
        _press_key(pressDown)
        
        _wait(17,19)
        
            
def test():
    entire_screen_bbox = Region(9, 237, 940, 700)
    
    xmin, xmax, ymin, ymax = 9000, 0, 9000, 0
    if entire_screen_bbox.exists(os.getcwd() + r'\images\agility_green.png'):
        pattern = Pattern(os.getcwd() + r'\images\agility_green.png')
        pattern.similar(0.95)
        matches = entire_screen_bbox.findAll(pattern)
        idx = 0
        while True:
            if not matches.hasNext():
                break
            m = matches.next()
            
            print(m)
            m = m.center
            
            if m.getX() < xmin:
                xmin = m.getX()
            elif m.getX() > xmax:
                xmax = m.getX()
            if m.getY() < ymin:
                ymin = m.getY()
            elif m.getY() > ymax:
                ymax = m.getY()
                
    
        
        newRegion = Region(xmin, ymin, xmax-xmin, ymax-ymin)
        newRegion.highlight()
    raw_input('Ready')



def _prep_cleanup():
    mySignal = signal.SIGINT
    currSignalFunc = signal.getsignal(mySignal)
    def mySignalFunc(*args, **kwargs):
        print('In my signal func')
        _cleanup()
        currSignalFunc(*args, **kwargs)
    signal.signal(mySignal, mySignalFunc)

def _cleanup():
    print('In cleanup')
    keyUp()
    try:
        _show_cursor()
    except:
        pass

if __name__ == "__main__":
    '''
    To enable stop signals to be caught:
    In PyCharm hit Ctrl + Shift + A to bring up the "Find Actions..." menu
    Search for "Registry" and hit enter
    Find the key kill.windows.processes.softly and enable it (you can start typing "kill" and it will search for the key)
    Restart PyCharm
    
    Stop signals will now be sent as SIGINT
    '''
    print('Make sure verticle camera is set')
    if sys.argv[1] in locals():
        Settings.ActionLogs = False
        try:
            _show_cursor()
        except:
            pass
        _prep_cleanup()
        try:
            eval(sys.argv[1])()
            beep(500)
        except:
            _cleanup()
            for _ in range(3):
                beep(200)
            raise