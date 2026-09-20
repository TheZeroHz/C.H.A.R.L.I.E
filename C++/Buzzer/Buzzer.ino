// CHARLIE buzzer bark — RTTTL player
// Pin 13 passive buzzer (use tone-capable GPIO)

#include <Arduino.h>

static const int BUZZER_PIN = 13;

// RTTTL: name:d=default_duration,o=default_octave,b=bpm:notes...
// Short descending chirps ≈ dog bark / woof
static const char *BARK_RTTTL =
    "Bark:d=16,o=5,b=200:"
    "c6,e5,g5,p,"
    "c6,e5,g5,p,"
    "d6,f5,a5,p,"
    "c6,e5,g5";

static const uint16_t NOTE_FREQ[] = {
    0,    // rest / unused
    262,  // C4
    277,  // C#4
    294,  // D4
    311,  // D#4
    330,  // E4
    349,  // F4
    370,  // F#4
    392,  // G4
    415,  // G#4
    440,  // A4
    466,  // A#4
    494,  // B4
};

static int noteIndex(char note) {
  switch (note) {
    case 'c': return 1;
    case 'd': return 3;
    case 'e': return 5;
    case 'f': return 6;
    case 'g': return 8;
    case 'a': return 10;
    case 'b': return 12;
    case 'p': return 0;
    default:  return -1;
  }
}

static uint16_t noteFrequency(int note, int octave) {
  if (note <= 0) {
    return 0;
  }
  // NOTE_FREQ is octave 4; scale by 2^(octave-4)
  uint16_t freq = NOTE_FREQ[note];
  if (octave > 4) {
    freq <<= (octave - 4);
  } else if (octave < 4) {
    freq >>= (4 - octave);
  }
  return freq;
}

// Play one RTTTL string. Blocking.
void playRtttl(int pin, const char *rtttl) {
  const char *p = rtttl;

  // Skip name until ':'
  while (*p && *p != ':') {
    p++;
  }
  if (*p == ':') {
    p++;
  }

  // Defaults
  int defaultDuration = 4;
  int defaultOctave = 6;
  int bpm = 63;

  // Parse header: d=, o=, b=
  while (*p) {
    if (*p == ':') {
      p++;
      break;
    }

    char key = *p++;
    if (*p == '=') {
      p++;
    }

    int value = 0;
    while (*p >= '0' && *p <= '9') {
      value = value * 10 + (*p++ - '0');
    }

    if (key == 'd') {
      defaultDuration = value;
    } else if (key == 'o') {
      defaultOctave = value;
    } else if (key == 'b') {
      bpm = value;
    }

    if (*p == ',') {
      p++;
    }
  }

  // Whole-note duration in ms: (60s / bpm) * 4 beats
  const unsigned long wholeNoteMs = (60UL * 1000UL * 4UL) / (unsigned long)bpm;

  while (*p) {
    // Optional duration prefix
    int duration = 0;
    while (*p >= '0' && *p <= '9') {
      duration = duration * 10 + (*p++ - '0');
    }
    if (duration == 0) {
      duration = defaultDuration;
    }

    // Note letter
    char noteChar = *p;
    if (noteChar >= 'A' && noteChar <= 'Z') {
      noteChar = noteChar - 'A' + 'a';
    }
    int note = noteIndex(noteChar);
    if (*p) {
      p++;
    }

    // Optional sharp
    if (*p == '#') {
      if (note > 0) {
        note++;
      }
      p++;
    }

    // Optional dotted note
    bool dotted = false;
    if (*p == '.') {
      dotted = true;
      p++;
    }

    // Optional octave
    int octave = defaultOctave;
    if (*p >= '0' && *p <= '9') {
      octave = *p++ - '0';
    }

    // Skip separators
    while (*p == ',' || *p == ' ') {
      p++;
    }

    unsigned long noteMs = wholeNoteMs / (unsigned long)duration;
    if (dotted) {
      noteMs += noteMs / 2;
    }

    uint16_t freq = noteFrequency(note, octave);
    if (freq > 0) {
      tone(pin, freq, noteMs);
      delay(noteMs);
      noTone(pin);
    } else {
      delay(noteMs);  // rest
    }

    // Tiny gap between notes so bark syllables separate
    delay(noteMs / 10);
  }

  noTone(pin);
}

void bark() {
  playRtttl(BUZZER_PIN, BARK_RTTTL);
}

void setup() {
  pinMode(BUZZER_PIN, OUTPUT);
  digitalWrite(BUZZER_PIN, LOW);
  Serial.begin(115200);
  delay(200);
  Serial.println("CHARLIE RTTTL bark ready");
  bark();
}

void loop() {
  // Re-bark every 4s — remove this when you trigger from sensors
  delay(4000);
  bark();
}
