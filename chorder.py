from types import SimpleNamespace as SimpleNS

import numpy as np
import simpleaudio as sa


class Chorder:
  ROOT_NOTES = {
      'A': 0,
      'A♯(B♭)': 1,
      'B': 2,
      'C': 3,
      'C♯(D♭)': 4,
      'D': 5,
      'D♯(E♭)': 6,
      'E': 7,
      'F': 8,
      'F♯(G♭)': 9,
      'G': 10,
      'G♯(A♭)': 11
  }
  COMPONTENTS = {
      '': np.array([0, 4, 7]),
      'm': np.array([0, 3, 7]),
      'dim': np.array([0, 3, 6]),
      'aug': np.array([0, 4, 8]),
      'sus2': np.array([0, 2, 7]),
      'sus4': np.array([0, 5, 7]),
      '7': np.array([0, 4, 7, 10]),
      'M7': np.array([0, 4, 7, 11]),
      'm7': np.array([0, 3, 7, 10]),
      'mM7': np.array([0, 3, 7, 11]),
      'dim7': np.array([0, 3, 6, 9]),
  }
  INSRTUMENTS = {
      # string_notes: 개방현 음표
      # string_intervals: 표준 A(440Hz) 기준 개방현의 음정(반음의 개수). 숫자가 클 수로 음이 낮아짐
      # num_frets: 프랫 개수
      'Ukulele': SimpleNS(string_notes=(0, 7, 3, 10), string_intervals=(0, 5, 9, 2), num_frets=19)
  }
  FRET_RATIO = 1.0 / pow(2.0, 1.0 / 12.0)

  _BASE_PITCH = 440
  _NUM_NOTES = 12
  _PITCH_RATIO = pow(0.5, 1.0 / 12.0)
  _SAMPLE_RATE = 44100

  def __init__(self, instrument: str, fret_limit: int = 5):
    self._instrument = self.INSRTUMENTS[instrument]
    self._num_strings = len(self._instrument.string_notes)
    self._fret_limit = fret_limit

  @property
  def num_strings(self):
    return self._num_strings

  def notes(self, frets):
    return self._note(frets, self._instrument.string_notes)

  def compose(self, root: str, comp: str, root_strings: list = None, max_root_fret: int = None):
    # 근음 음표
    root_note = self.ROOT_NOTES[root]

    # 구성음 음표
    comp_notes = set(self._note(self.COMPONTENTS[comp], root_note))

    if root_strings is None:
      root_strings = range(self._num_strings)
    if max_root_fret is None:
      max_root_fret = self._instrument.num_frets

    chords = []
    for root_string in root_strings:
      string_note = self._instrument.string_notes[root_string]
      for root_fret in range(root_note - string_note, self._instrument.num_frets, self._NUM_NOTES):
        if root_fret >= 0 and root_fret <= max_root_fret:
          chords += self._compose(root_string, root_fret, root_note, comp_notes)
    return np.unique(chords, axis=0)

  def play(self, chord: list, seconds: float = 1):
    t = np.linspace(0, seconds, seconds * self._SAMPLE_RATE, False)
    pitches = self._pitches(chord)
    harmony = np.sum([np.sin(pitch * t * 2 * np.pi) for pitch in pitches], axis=0) / len(pitches)
    audio = harmony * (2**15 - 1) / np.max(np.abs(harmony))
    audio = audio.astype(np.int16)
    play_obj = sa.play_buffer(audio, 1, 2, self._SAMPLE_RATE)
    play_obj.wait_done()


  def _note(self, fret, string_note):
    return (fret + string_note) % self._NUM_NOTES

  def _pitches(self, frets):
    return self._BASE_PITCH * np.power(self._PITCH_RATIO, (self._instrument.string_intervals - frets))

  def _compose(self, root_string: int, root_fret: int, root_note: int, comp_notes: set):
    string_frets = tuple([] for _ in range(self._num_strings))
    string_frets[root_string].append(root_fret)
    fret_range = range(max(root_fret - self._fret_limit, 0),
                       min(root_fret + self._fret_limit + 1, self._instrument.num_frets + 1))
    for string in range(self._num_strings):
      if string != root_string:
        string_note = self._instrument.string_notes[string]
        for fret in fret_range:
          if self._note(fret, string_note) in comp_notes:
            string_frets[string].append(fret)

    chords = []
    for candiate in np.array(np.meshgrid(*string_frets)).T.reshape(-1, self._num_strings):
      num_comps = len(np.unique(self.notes(candiate)))
      if num_comps == len(comp_notes) and np.ptp(candiate) <= self._fret_limit:
        chords.append(candiate)
    return chords


# #%%
# chorder = Chorder('Ukulele')
# root = 'B' # ♯♭
# chord = 'mM7'
# chords = chorder.compose(root, chord, max_root_fret=7)

# #%%
# 440 * pow(1.059, 9)
# #%%
