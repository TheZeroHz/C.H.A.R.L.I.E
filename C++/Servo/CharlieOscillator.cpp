#include "CharlieOscillator.h"

bool CharlieOscillator::next_sample() {
  _currentMillis = millis();
  if (_currentMillis - _previousMillis > _samplingPeriod) {
    _previousMillis = _currentMillis;
    return true;
  }
  return false;
}

int CharlieOscillator::attach(int pin, bool rev) {
  if (_attached && _pin == pin) {
    return _channel;
  }
  if (_attached) {
    detach();
  }

  _pin = pin;
  _rev = rev;
  _servo.setPeriodHertz(50);
  // Wider pulse range helps picky MG90S clones
  _channel = _servo.attach(pin, 500, 2500);
  if (_channel < 0) {
    // Retry once — ESP32-S3 LEDC can fail transiently
    delay(5);
    _channel = _servo.attach(pin, 500, 2500);
  }

  _attached = (_channel >= 0);
  if (!_attached) {
    return -1;
  }

  _pos = 90;
  _servo.write(90);
  _previousServoCommandMillis = millis();

  _samplingPeriod = 30;
  _period = 2000;
  _numberSamples = _period / (double)_samplingPeriod;
  _inc = 2.0 * M_PI / _numberSamples;
  _previousMillis = 0;

  _amplitude = 45;
  _phase = 0;
  _phase0 = 0;
  _offset = 0;
  _stop = false;
  return _channel;
}

void CharlieOscillator::detach() {
  if (_attached) {
    _servo.detach();
    _attached = false;
    _channel = -1;
  }
}

void CharlieOscillator::SetT(unsigned int T) {
  _period = T;
  _numberSamples = _period / (double)_samplingPeriod;
  _inc = 2.0 * M_PI / _numberSamples;
}

void CharlieOscillator::SetPosition(int position) {
  write(position);
}

void CharlieOscillator::refresh() {
  if (next_sample()) {
    if (!_stop) {
      int pos = (int)round(_amplitude * sin(_phase + _phase0) + _offset);
      if (_rev) {
        pos = -pos;
      }
      write(pos + 90);
    }
    _phase += _inc;
  }
}

void CharlieOscillator::write(int position) {
  const unsigned long now = millis();

  if (_diff_limit > 0) {
    const int elapsed = (int)(now - _previousServoCommandMillis);
    const int limit = max(1, (elapsed * _diff_limit) / 1000);
    if (abs(position - _pos) > limit) {
      _pos += (position < _pos) ? -limit : limit;
    } else {
      _pos = position;
    }
  } else {
    _pos = position;
  }

  _previousServoCommandMillis = now;

  int out = _pos + _trim;
  if (out < 0) out = 0;
  if (out > 180) out = 180;
  _servo.write(out);
}
