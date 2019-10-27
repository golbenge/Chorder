import math
from types import SimpleNamespace as SimpleNS

from kivy.app import App
from kivy.graphics import Color, Ellipse, Line, PopMatrix, PushMatrix, Scale, Translate
from kivy.uix.label import Label
from kivy.uix.widget import Widget

from chorder import Chorder


class ChordView(Widget):
  _STRING_MARGIN = 0.02
  _STRING_LENGTH = 0.8
  _FREST_START_X = (1.0 - _STRING_LENGTH) * 0.5
  _STRING_START_X = _FREST_START_X - _STRING_MARGIN
  _STRING_END_X = _FREST_START_X + _STRING_LENGTH + _STRING_MARGIN

  _FRET_LENGTH = 0.5
  _FRET_START_Y = (1.0 - 0.5) * 0.5
  _FRET_END_Y = _FRET_START_Y + _FRET_LENGTH

  _FINGER_SIZE = 0.05
  _LABEL_SIZE = 40

  def __init__(self, chorder, chord, root, **kwargs):
    super().__init__(**kwargs)
    self._chorder = chorder
    self._chord = chord
    self._prepare(root)
    self.draw_chord()
    self.bind(pos=self.draw_chord, size=self.draw_chord)

  def draw_chord(self, *args):
    self.canvas.clear()
    with self.canvas:
      PushMatrix()
      Translate(self.x, self.y)
      Scale(self.width, self.height, 1)
      Color(1, 1, 1)
      for fret_pos in self._fret_pos:
        Line(points=(fret_pos, self._FRET_START_Y, fret_pos, self._FRET_END_Y))
      if self._min_fret == 0:
        Line(points=(self._STRING_START_X, self._FRET_START_Y, self._STRING_START_X, self._FRET_END_Y))
      Label(text='1')
      finger_size = (self._FINGER_SIZE, self.width / self.height * self._FINGER_SIZE)
      for string, finger in zip(self._string_pos, self._fingers):
        if finger.root:
          Color(1.0, 0.0, 0.0)
        else:
          Color(1.0, 1.0, 1.0)
        Line(points=(self._STRING_START_X, string, self._STRING_END_X, string))
        Color(1.0, 1.0, 1.0)
        if finger.pos is not None:
          Ellipse(pos=(finger.pos[0] - finger_size[0] * 0.5, finger.pos[1] - finger_size[1] * 0.5),
                  size=finger_size)
      PopMatrix()
    self.clear_widgets()
    label_pos_y = self._string_pos[-1] * self.height - self._LABEL_SIZE + self.y
    for fret_idx, fret_pos in enumerate(self._fret_pos):
      self.add_widget(
          Label(text=f'{self._min_fret+fret_idx}',
                text_size=(self._LABEL_SIZE, self._LABEL_SIZE),
                pos=(float(fret_pos) * self.width - self._LABEL_SIZE * 0.5 + self.x, label_pos_y),
                size=(self._LABEL_SIZE, self._LABEL_SIZE),
                halign='center',
                valign='top'))

  def on_touch_down(self, touch):
    if self.collide_point(*touch.pos):
      self._chorder.play(self._chord)
      return True
    else:
      return super().on_touch_down(touch)

  @property
  def _notes(self):
    return self._chorder.notes(self._chord)

  def _prepare(self, root):
    self._min_fret = max(min(self._chord) - 1, 0)
    num_frets = max(5, max(self._chord) - self._min_fret)
    first_fret_dist = (self._STRING_LENGTH * (1 - Chorder.FRET_RATIO) /
                       (1.0 - pow(Chorder.FRET_RATIO, num_frets)))
    fret_pos = self._FREST_START_X
    self._fret_pos = [fret_pos]
    for fret in range(num_frets):
      fret_pos += first_fret_dist * pow(Chorder.FRET_RATIO, fret)
      self._fret_pos.append(fret_pos)
    string_space = self._FRET_LENGTH / (self._chorder.num_strings - 1)
    self._string_pos = [(self._chorder.num_strings - string - 1) * string_space + self._FRET_START_Y
                        for string in range(self._chorder.num_strings)]
    self._fingers = []
    root_note = Chorder.ROOT_NOTES[root]
    for fret, string_pos, note in zip(self._chord, self._string_pos, self._notes):
      if fret == 0:
        self._fingers.append(SimpleNS(pos=None, root=(note == root_note)))
      else:
        idx = fret - self._min_fret
        pos_x = (self._fret_pos[idx] + self._fret_pos[idx - 1]) * 0.5
        self._fingers.append(SimpleNS(pos=(pos_x, string_pos), root=(note == root_note)))


class ChorderApp(App):
  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self._chorder = Chorder('Ukulele')

  def compose(self, root: str, comp: str):
    chords = self._chorder.compose(root, comp, max_root_fret=7)
    self.root.chord_views.clear_widgets()
    self.root.chord_views.cols = int(math.ceil(math.sqrt(len(chords))))
    for chord in chords:
      self.root.chord_views.add_widget(ChordView(self._chorder, chord, root))

  def on_start(self):
    self.compose(self.root.root_note.text, self.root.comp_name.text)


if __name__ == '__main__':
  ChorderApp().run()
