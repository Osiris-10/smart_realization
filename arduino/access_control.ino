/*
 * Code Arduino pour le contrôle d'accès
 * LED verte = Accès autorisé
 * LED rouge = Accès refusé
 * Buzzer = Signal sonore
 * 
 * Connexions:
 * - LED verte: Pin 10 (avec résistance 220Ω)
 * - LED rouge: Pin 11 (avec résistance 220Ω)
 * - Buzzer: Pin 9
 * 
 * Commandes série:
 * - 'G' = Accès autorisé (LED verte + bip court)
 * - 'R' = Accès refusé (LED rouge + bip long)
 * - 'O' = Tout éteindre
 */

const int LED_VERTE = 10;
const int LED_ROUGE = 11;
const int BUZZER = 9;

void setup() {
  // Initialiser les pins
  pinMode(LED_VERTE, OUTPUT);
  pinMode(LED_ROUGE, OUTPUT);
  pinMode(BUZZER, OUTPUT);
  
  // Tout éteindre au démarrage
  digitalWrite(LED_VERTE, LOW);
  digitalWrite(LED_ROUGE, LOW);
  digitalWrite(BUZZER, LOW);
  
  // Initialiser la communication série
  Serial.begin(9600);
  
  // Signal de démarrage
  testSequence();
}

void loop() {
  // Vérifier si une commande est reçue
  if (Serial.available() > 0) {
    char command = Serial.read();
    
    switch (command) {
      case 'G':  // Accès autorisé
        accessGranted();
        break;
        
      case 'R':  // Accès refusé
        accessDenied();
        break;
        
      case 'O':  // Tout éteindre
        allOff();
        break;
    }
  }
}

void accessGranted() {
  // Éteindre LED rouge
  digitalWrite(LED_ROUGE, LOW);
  
  // Allumer LED verte
  digitalWrite(LED_VERTE, HIGH);
  
  // Bip court (succès)
  tone(BUZZER, 1000, 200);  // 1000Hz pendant 200ms
  delay(300);
  tone(BUZZER, 1500, 200);  // 1500Hz pendant 200ms
  
  // Garder la LED verte allumée pendant 3 secondes
  delay(3000);
  
  // Éteindre
  digitalWrite(LED_VERTE, LOW);
}

void accessDenied() {
  // Éteindre LED verte
  digitalWrite(LED_VERTE, LOW);
  
  // Allumer LED rouge
  digitalWrite(LED_ROUGE, HIGH);
  
  // Bip long (erreur) - 3 bips
  for (int i = 0; i < 3; i++) {
    tone(BUZZER, 500, 300);  // 500Hz pendant 300ms
    delay(400);
  }
  
  // Garder la LED rouge allumée pendant 3 secondes
  delay(2000);
  
  // Éteindre
  digitalWrite(LED_ROUGE, LOW);
}

void allOff() {
  digitalWrite(LED_VERTE, LOW);
  digitalWrite(LED_ROUGE, LOW);
  noTone(BUZZER);
}

void testSequence() {
  // Test au démarrage
  digitalWrite(LED_VERTE, HIGH);
  tone(BUZZER, 1000, 100);
  delay(200);
  digitalWrite(LED_VERTE, LOW);
  
  digitalWrite(LED_ROUGE, HIGH);
  tone(BUZZER, 800, 100);
  delay(200);
  digitalWrite(LED_ROUGE, LOW);
  
  // Prêt
  Serial.println("Arduino Ready");
}
