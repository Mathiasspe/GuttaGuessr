# 📸 PhotoGuessr

A multiplayer GeoGuessr-style game using your own photos. One screen shows the photo, everyone guesses the location on their phone. Built with Firebase Realtime Database and Leaflet.js — hosted for free on GitHub Pages.

## How it works

A host opens the game on a TV or shared screen. Players join on their phones using a 4-character room code. Each round, a photo is displayed on the host screen while players see only a map on their phone where they place their guess. After the timer runs out (or everyone submits), the results show the actual location, all guesses, distances, and points.

### Scoring

Points are calculated using an exponential decay formula based on distance:

```
points = 5000 × e^(-distance_km / decay)
```

The `decay` value controls strictness. With `decay = 2` (the default), being 50m away earns ~4900 points while 5km off gives only ~400. Adjust this in `host.html` by changing the value in the `calcPoints` function. Lower values are stricter.

| Decay | 50m | 500m | 1km | 5km | 10km |
|-------|-----|------|-----|-----|------|
| 2 | 4877 | 3894 | 3033 | 410 | 34 |
| 5 | 4950 | 4524 | 4094 | 1839 | 676 |
| 50 | 4950 | 4901 | 4756 | 3033 | 1839 |

Distance is calculated using the Haversine formula (great-circle distance on a sphere).

## Files

```
photoguessr/
├── host.html           ← Open on TV/shared screen
├── player.html         ← Players open on their phones
├── extract_gps.html    ← Tool for extracting GPS from photos
├── README.md
└── photos/
    ├── IMG_1234.jpg
    ├── IMG_5678.jpg
    └── ...
```

**host.html** — Controls the game. Shows the lobby with room code, displays photos during rounds, shows results with a map of all guesses, and the final leaderboard.

**player.html** — The phone interface. Players enter the room code and their name to join, then place a pin on the map each round. Shows a confirmation screen after submitting and round results with their score.

**extract_gps.html** — A browser-based tool that reads GPS coordinates from photo EXIF data. Drop your photos in, verify the location on a mini map per photo (drag to correct if off), edit hints, and copy the generated config into `host.html`. Runs entirely in the browser — no server, no upload.

## Setup

### 1. Firebase (free tier)

1. Create a project at [console.firebase.google.com](https://console.firebase.google.com)
2. Enable **Realtime Database** (not Firestore)
3. Set database rules to:
   ```json
   {
     "rules": {
       ".read": true,
       ".write": true
     }
   }
   ```
4. Register a web app (Project Settings → Your apps → Web)
5. Copy the `firebaseConfig` object into both `host.html` and `player.html`, replacing the placeholder

### 2. Photos

1. Export photos from iCloud (download originals to preserve GPS EXIF data)
2. Put them in the `photos/` folder
3. Open `extract_gps.html` in your browser
4. Drop the photos from `photos/` onto the page
5. Verify each location on the mini map — drag the marker to correct if needed
6. Copy the generated `PHOTOS` array and paste it into `host.html`, replacing the example array

### 3. Deploy

1. Create a GitHub repository and push all files
2. Enable GitHub Pages: Settings → Pages → Source: Deploy from a branch → main
3. The game is live at `https://yourusername.github.io/reponame/host.html`

## Game flow

1. Host opens `host.html` on a shared screen → a room code appears
2. Players open `player.html` on their phones → enter room code + name
3. Host configures rounds (5/10/15) and time limit (30s–120s or unlimited)
4. Host starts the game
5. Each round:
   - Photo appears on the host screen only
   - Players see a world map on their phone and tap to place a pin
   - Timer counts down (synced via Firebase)
   - When all players submit or time runs out, results are shown
   - Map displays actual location (green) and all guesses (colored) with distance lines
   - Points awarded based on proximity
6. After all rounds, a final leaderboard shows total scores

## Tech stack

- **Firebase Realtime Database** — syncs game state, guesses, and scores across all devices in real-time
- **Leaflet.js + OpenStreetMap** — free maps with no API key required
- **ExifReader** — client-side EXIF parsing for GPS extraction
- **GitHub Pages** — free static hosting for the game and photos

No build step, no dependencies to install, no backend server. Everything runs in the browser.

## Firebase data structure

```
rooms/
  {ROOM_CODE}/
    state: 'lobby' | 'playing' | 'finished'
    roundState: 'guessing' | 'results'
    currentRound: number
    settings: { totalRounds, timeLimit }
    players/
      {playerId}/
        name: string
        totalScore: number
    photos: [{ url, lat, lng, hint }]
    guesses/
      round_{N}/
        {playerId}: { lat, lng, submittedAt }
    results/
      round_{N}: [{ name, distance, points }]
    timeLeft: number
```
