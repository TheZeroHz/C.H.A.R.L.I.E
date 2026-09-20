//--------------------------------------------------------------
// CharlieOscillator — Otto-style sinusoidal servo driver
// Based on Oscillator by Juan Gonzalez-Gomez (Obijuan) / OttoDIY
// Rate limiter reduces peak current (same idea as Otto SetLimiter)
//--------------------------------------------------------------
#ifndef CharlieOscillator_h
#define CharlieOscillator_h

#include <Arduino.h>
#include <ESP32Servo.h>
#include <math.h>

#ifndef DEG2RAD
#define DEG2RAD(g) ((g) * M_PI / 180.0)
#endif

class CharlieOscillator {
public:
  CharlieOscillator(int trim = 0)
      : _trim(trim), _diff_limit(0), _pos(90), _stop(true), _rev(false) {}

  // returns LEDC channel (>=0) or -1 on failure
  int attach(int pin, bool rev = false);
  void detach();
  // ESP32Servo::attached() is non-const, so track it ourselves
  bool attached() const { return _attached; }
  int pin() const { return _pin; }
  int channel() const { return _channel; }

  void SetA(unsigned int amplitude) { _amplitude = amplitude; }
  void SetO(int offset) { _offset = offset; }
  void SetPh(double ph) { _phase0 = ph; }
  void SetT(unsigned int period);
  void SetTrim(int trim) { _trim = trim; }
  void SetLimiter(int diff_limit) { _diff_limit = diff_limit; }
  void DisableLimiter() { _diff_limit = 0; }

  int getTrim() const { return _trim; }
  int getPosition() const { return _pos; }

  void SetPosition(int position);
  void Stop() { _stop = true; }
  void Play() { _stop = false; }
  void Reset() { _phase = 0; }
  void refresh();

private:
  bool next_sample();
  void write(int position);

  Servo _servo;

  unsigned int _amplitude = 45;
  int _offset = 0;
  unsigned int _period = 2000;
  double _phase0 = 0;

  int _pos;
  int _trim;
  double _phase = 0;
  double _inc = 0;
  double _numberSamples = 0;
  unsigned int _samplingPeriod = 30;

  unsigned long _previousMillis = 0;
  unsigned long _currentMillis = 0;
  unsigned long _previousServoCommandMillis = 0;

  bool _stop;
  bool _rev;
  bool _attached = false;
  int _pin = -1;
  int _channel = -1;
  int _diff_limit;  // max deg/sec; 0 = off
};

#endif
