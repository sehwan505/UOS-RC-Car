char Direction;
bool isMoving = false;

byte DataToRead[5];

void setup() {
  Serial.begin(9600);
  pinMode(4, OUTPUT);
  pinMode(5, OUTPUT);
  pinMode(6, OUTPUT);
  pinMode(7, OUTPUT);
  pinMode(8, OUTPUT);
  pinMode(9, OUTPUT);
}

void loop() {
  if (Serial.available() > 0) {
    Serial.readBytesUntil(char(13), DataToRead, 5);
    DataToRead[4] = '\n';
    Direction = DataToRead[0];
    isMoving = true;  // 입력이 들어오면 움직임 상태로 변경
  }
  
  if (isMoving) {
    moveMotor(Direction);
    analogWrite(8, 0);
    analogWrite(9, 0);
    digitalWrite(4, LOW);
    digitalWrite(5, LOW);
    digitalWrite(6, LOW);
    digitalWrite(7, LOW);
    isMoving = false;  // 움직임 상태를 false로 변경
    Serial.println("moved");
  }
}

void moveMotor(char direction) {
  digitalWrite(4, HIGH);
  digitalWrite(5, LOW);
  digitalWrite(6, HIGH);
  digitalWrite(7, LOW);

  switch(direction){
    case 'F': { analogWrite(8, 130); analogWrite(9, 255); delay(100); analogWrite(8, 0); delay(80); break; }
    case 'L': { digitalWrite(4, LOW); digitalWrite(5, HIGH); analogWrite(8, 130); analogWrite(9, 255); delay(80); analogWrite(8, 0); delay(100); break; }
    case 'R': { digitalWrite(6, LOW); digitalWrite(7, HIGH); analogWrite(8, 130); analogWrite(9, 255); delay(100); analogWrite(8, 0); delay(80); break; }
    case 'l': { analogWrite(8, 130); analogWrite(9, 255); delay(50); analogWrite(8, 0); delay(120); break; }
    case 'r': { analogWrite(8, 130); analogWrite(9, 255); delay(160); break; }
    case 'S': { analogWrite(8, 0); analogWrite(9, 0); delay(2000); break; }
    default: break;
  }
}