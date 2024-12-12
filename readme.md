```git clone https://github.com/SalupovTeam/statuspage
cd statuspage
docker build -t statuspage . 
docker run -d -p 1487:1487 --name statuspage statuspage
sleep 1
docker logs statuspage
```

Make sure to replace logo in templates/logo.png with your own :)
