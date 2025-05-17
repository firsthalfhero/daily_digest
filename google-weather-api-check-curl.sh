$uri = "https://weather.googleapis.com/v1/forecast/days:lookup?key=AIzaSyCEHCsRlpq19IzjvYtRvdPbMzmWRyAQuP0&location.latitude=-33.8688&location.longitude=151.2093&days=7&units=METRIC&languageCode=en"
$response = Invoke-RestMethod -Uri $uri -Method Get
$response