# Cerințe Proiect

## MODUL ANALIZĂ

1. Descrierea modelului ales și a obiectivelor aplicației
2. Diagramele bazei de date OLTP inițiale, care va fi utilizată ca bază pentru distribuirea datelor:
    * Diagrama entitate – relație a bazei de date OLTP inițiale (minim 10 entități independente; minim o relație de tip many-to-many; normalizare FN3)
    * Diagrama conceptuală a bazei de date OLTP inițiale
3. Descrierea modului de distribuire (numărul de server-e de baze de date din rețea)
4. Argumentarea deciziei de fragmentare a relațiilor:
    * Fragmentare orizontală primară: Aplicarea algoritmului de fragmentare orizontală primară (exemplificarea pașilor algoritmului pe baza unor date ipotetice) și obținerea fragmentelor orizontale primare
    * Fragmentare orizontală derivată: Obținerea fragmentelor orizontale derivate
    * Fragmentare verticală: Aplicarea algoritmului de fragmentare verticală (exemplificarea pașilor algoritmului pe baza unor date ipotetice) și obținerea fragmentelor verticale
    * Verificarea corectitudinii fragmentărilor realizate
5. Argumentarea deciziei de replicare a anumitor relații sau/și de stocare a unei relații pe o singură stație
6. Crearea schemelor conceptuale locale (corespunzătoare bazelor de date locale)
7. Lista tuturor constrângerilor ce trebuie îndeplinite de model:
    * Unicitate: unicitate locală, unicitate globală pe fragmente orizontale, unicitate globală în cazul în care trebuie să fie unică o combinație de coloane care se găsesc în fragmente verticale diferite (specificându-se argumentele care au stat la baza acestei decizii din punct de vedere al optimizării)
    * Cheie primară (la nivel local/global)
    * Cheie externă (la nivel local și pentru relații stocate în baze de date diferite)
    * Validare (la nivel local și pentru relații stocate în baze de date diferite)
8. Formularea în limbaj natural a unei cereri SQL complexe care va folosi date din mai multe fragmente și va fi optimizată în etapa de implementare
9. Precizarea tehnicilor de optimizare ce ar putea fi utilizate pentru această cerere particulară (avantaje / dezavantaje de utilizare pentru o anumită tehnică)

---

## MODUL IMPLEMENTARE BAZE DE DATE – MODUL BACK-END

1. Crearea bazelor de date și a utilizatorilor
2. Crearea relațiilor și a fragmentelor
3. Popularea cu date a bazelor de date
4. Furnizarea formelor de transparență pentru întreg modelul ales:
    * transparență pentru fragmentele verticale
    * transparență pentru fragmentele orizontale
    * transparență pentru tabelele stocate în altă bază de date față de cea la care se conectează aplicația
5. Asigurarea sincronizării datelor pentru relațiile replicate
6. Asigurarea tuturor constrângerilor de integritate folosite în model (atât la nivel local, cât și la nivel global)
7. Optimizarea cererii SQL propusă în raportul de analiză:
    * planul de execuție ales de optimizatorul bazat pe regulă (explicație etape parcurse)
    * planul de execuție ales de optimizatorul bazat pe cost (explicație etape parcurse)
    * sugestii de optimizare a cererii, specificând planul de execuție obținut

---

## ETAPA IMPLEMENTARE APLICAȚIE – FRONT-END

1. Modul aplicație prin care se introduc și gestionează informații la nivelul bazelor de date locale
2. Modul aplicație prin care se vizualizează informații la nivelul bazei de date globale
3. Posibilitatea de vizualizare la nivelul bazei de date globale a modificărilor aplicate asupra datelor stocate în bazele de date locale (efectele operațiilor LMD locale realizate pe fragmentele orizontale, pe fragmentele verticale, respectiv pe relațiile replicate)
4. Posibilitatea de verificare la nivelul bazelor de date locale a propagării operațiilor LMD realizate la nivelul bazei de date globale (efectele operațiilor LMD realizate la nivel global ce se vor reflecta asupra fragmentelor orizontale, a fragmentelor verticale, respectiv a relațiilor replicate)
