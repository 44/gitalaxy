function randomInt(max) {
  return Math.floor(Math.random() * max);
}

const started = new Date();
var lastShown = 0;
let daysPerSecond = 7;

function createStars(width, height, spacing) {
  const stars = {};

  for (let x = 0; x < width; x += spacing) {
    for (let y = 0; y < height; y += spacing) {
      const star = {
        x: x + randomInt(spacing),
        y: y + randomInt(spacing),
        r: Math.random() * maxStarRadius
      };
      const key = star.x.toString() + ":" + star.y.toString();
      stars[key] = star;
    }
  }
  return stars;
}

function initStars()
{
    return new Map();
}

function fillCircle(ctx, x, y, r, fillStyle) {
  ctx.beginPath();
  ctx.fillStyle = fillStyle;
  ctx.arc(x, y, r, 0, Math.PI * 2);
  ctx.fill();
}

function getOpacity(factor) {
  const opacityIncrement =
    (maxStarOpacity - minStarOpacity) * Math.abs(Math.sin(factor));
  const opacity = minStarOpacity + opacityIncrement;
  return opacity;
}

function projectDate(ts) {
    var diff = (ts - state.checkpoint[0]) / 1000 * daysPerSecond;
    var curDate = new Date(state.checkpoint[1].getTime() + diff * 24 * 60 * 60 * 1000);
    return curDate;
}

function renderMeteors(ctx, diff) {
    ctx.strokeStyle = "rgba(255,255,255,0.5)";
    for (let m of state.meteors)
    {
        ctx.beginPath();
        ctx.moveTo(m.x, m.y);
        ctx.lineTo(m.x - m.dx*3, m.y - m.dy*3);
        ctx.stroke();
    }
    ctx.strokeStyle = "#fff";
    for (let m of state.meteors)
    {
        ctx.beginPath();
        ctx.moveTo(m.x, m.y);
        ctx.lineTo(m.x - m.dx, m.y - m.dy);
        ctx.stroke();
        m.x += m.dx / 10;
        m.y += m.dy / 10;
    }
    state.meteors = state.meteors.filter(m => (m.x > 0) && (m.x < width) && (m.y > 0) && (m.y < height));
}

function renderMoon(ctx, blur, ts) {
    if (moonReady) {
        const toCross = 500 * 1000;
        const rts = ts % toCross;
        let x = rts * (width + 200) / toCross;
        let a = height/2 - 50;
        a = a / (width/2 + 100);
        a = a / (width/2 + 100);
        const b = width/2 + 100;
        const c = 50;
        const y = a * (x - b) * (x - b) + c;
        // console.log('mooo', x, y, a, b, c, width, height);
        ctx.drawImage(moonImage, Math.floor(x), Math.floor(y), 30, 30);


        // y = a * (x - b)^2 + 50;
        // c = 50
        // b = w/2 + 100
        //
        // h/2 = a * (0 - w/2 - 100)^2 + 50;
        // a= (h/2 - 50)/(w/2 + 100)^2
        //
        //
        // 1) x = 0, y = height/2
        //
        // -> height/2 = c;
        //
        // 2) x = width/2 + 100, y = 50
        //
        // -> 50 = a * (width/2 + 100)^2 + b * (width/2 + 100) + h/2
        // -> b = (50 - h/w - a *(w/2+100)^2)/(w/2+100)
        //
        // 3) x = w+200, y = h/2
        //
        // -> 0 = a * (w+200)^2 + b * (w+200)
        // -> a = -b/(w+200)
        //
        // -> b = (50 - h/w + b/(w+200)*(w+200)^2)/(w/2+100)
        //
        //
        //
        //
    }
  // const period = 30;
  // var x = Math.floor(ts / 1000 * width / period) % (width + 200);
  // var y = Math.floor(height/3 - height / 3 * ts / 1000 / period / 2) % Math.floor(height / 3);
  // document.getElementById("moon").style.left = `${x}px`;
  // document.getElementById("moon").style.top = `${y}px`;
  // document.getElementById("moon").top = 
  // fillCircle(ctx, moon.x, moon.y, moon.r, moon.color);
  // // render a smaller circle above the moon to give it that well-known moon-shape
  // fillCircle(
  //   ctx,
  //   moon.x - moon.r / 3,
  //   moon.y - moon.r / 3,
  //   moon.r,
  //   backgroundColor
  // );

  // ctx.font = "30px Arial";
  // ctx.fillStyle = "white";
}

function applyDecay(curDate) {
    for (let n of stars.keys())
    {
        const star = stars.get(n);
        const daysFromLastHit = Math.floor((curDate.getTime() - star.l.getTime()) / 1000 / 60 / 60 / 24);
        if (daysFromLastHit < 30)
        {
            continue;
        }
        const daysFromLastDecay = Math.floor((curDate.getTime() - star.ld.getTime()) / 1000 / 60 / 60 / 24);
        if (daysFromLastDecay < 1)
        {
            continue;
        }
        const factor = (daysFromLastHit > 365) ? 5 : ((daysFromLastHit > 160) ? 2 : 1);
        star.d += daysFromLastDecay * factor;
        star.ld = curDate;

        if (star.d > star.h * 10)
        {
            state.removeQueue.add(n);
        }
    }
}

function assignColor(entry) {
    if (entry.c == "test")
    {
        return "196,255,196";
    } else if ((entry.c == "strings") || (entry.c == "omc") || (entry.c == "lcl")) {
        return "255,196,196";
    } else if (entry.c.includes("proj") || entry.c.includes("filters")) {
        return "196,196,255";
    } else if (entry.c == "h") {
        return "255,255,196";
    }
    return "255,255,255";
}

let lastShownStatus = "";

function updateStatus(curDate) {
    let cutoff = curDate.toISOString().substring(0, 10);
    let statusMessage = cutoff;
    if (daysPerSecond == 0) {
        statusMessage += " \udb80\udfe6 paused";
    } else if (daysPerSecond == 1) {
        statusMessage += " \udb83\udf86 d/s";
    } else if (daysPerSecond == 7) {
        statusMessage += " \udb83\udf85 w/s";
    } else if (daysPerSecond == 30) {
        statusMessage += " \udb81\udcc5 m/s";
    }
    if (lastShownStatus != statusMessage)
    {
        document.getElementById("status").innerHTML = statusMessage;
    }
}

let curMeteor = 0;

function updateStars(ts) {
    var curDate = projectDate(ts);
    var lastDate = projectDate(state.lastTs);
    updateStatus(curDate);
    if (curDate.getDate() == lastDate.getDate())
    {
        return;
    }

    let cutoff = curDate.toISOString().substring(0, 10);

    const frameTime= (ts - state.lastTs);
    applyDecay(curDate);

    state.lastTs = ts;
    let changed = 0;
    let removed = 0;
    let added = 0;

    for (let i = state.nextChangeToProcess; i < all_changes.length; i++) {
        const change = all_changes[i];
        if (change.date > cutoff) {
            break;
        }
        if (state.commitsByAuthor.has(change.author))
        {
            if (state.commitsByAuthor.get(change.author) > 100)
            {
                console.log("meteor requested:" + change.author);
                state.commitsByAuthor.set(change.author, 0);
                const mx = randomInt(width);
                const dx = (mx > width / 2) ? (-randomInt(15)) : (randomInt(15));
                state.meteors.push({x: mx, y: randomInt(height / 3), dx: dx, dy: 10 + randomInt(20)});
            }
            else
            {
                state.commitsByAuthor.set(change.author, state.commitsByAuthor.get(change.author) + 1);
            }
        }
        else
        {
            state.commitsByAuthor.set(change.author, 1);
        }
        state.message = " ";
        for (const s of change.on) {
            const key = s.x.toString() + ":" + s.y.toString();
            if (stars.has(key)) {
                const star = stars.get(key);
                star.r += 0.01;
                star.l = curDate;
                star.h++;
                star.ld = curDate;
                if (star.r > 3) {
                    if (state.highlight[0] != key) {
                        state.highlight = [s.fname, star.h];
                    }
                    star.r = 3;
                }
                changed++;
            } else {
                const star = {
                    n: s.fname,
                    x: s.x * width / 256 / 256,
                    y: s.y * height / 256 / 256,
                    r: 1.0, // radius - should be calculated from the number of hits and decay
                    l: curDate, // last hit
                    h: 1, // hits
                    d: 0, // decay
                    ld: curDate, // last decay
                    c: assignColor(s),
                };
                stars.set(key, star);
                state.stars++;
                added++;
            }
        }
        if (true) { // do not remove right away, let them decay
            for (const s of change.off) {
                const key = s.x.toString() + ":" + s.y.toString();
                if (stars.has(key)) {
                    state.removeQueue.add(key);
                }
            }
        }
        state.nextChangeToProcess = i + 1;
        // console.log("processed:", i, change.date, change.on.length, change.off.length);
    }

    const allowedDeletes = 500 * frameTime / 1000 * daysPerSecond;

    let deleted = 0;
    state.removeQueue.forEach(key => {
        if (deleted < allowedDeletes) {
            if (!stars.delete(key) ) {
                console.log("failed to delete", key);
            }
            state.removeQueue.delete(key);
            state.stars--;
            deleted++;
            removed++;
        }
    });
    state.message = "changed: " + changed + " added: " + added + " removed: " + removed;
    if ( (curDate.getFullYear() - state.end.getFullYear()) > 0)
    {
        console.log("auto-restart requested:" + (curDate.getTime()  - state.end.getTime()));
        state.restart = true;
    }
}

function drawStar(ctx, x, y, c) {
    ctx.fillStyle = `rgb(${c})`;
    const axes = [4,4,4,4];
    const update = randomInt(4);
    axes[update] = 6;
    ctx.beginPath();
    ctx.moveTo(x, y + axes[0]);
    ctx.lineTo(x + 1, y + 1);
    ctx.lineTo(x + axes[1], y);
    ctx.lineTo(x + 1, y - 1);
    ctx.lineTo(x, y - axes[2]);
    ctx.lineTo(x - 1, y - 1);
    ctx.lineTo(x - axes[3], y);
    ctx.lineTo(x - 1, y + 1);
    ctx.closePath();
    ctx.fill();
}

let lastHL = {
    x: 0,
    y: 0,
    c: "",
    n: "",
};

function render(ts) {
  updateStars(ts);
  ctx.fillStyle = backgroundColor;
  ctx.clearRect(0, 0, width, height);
  let cnt = 0;
  const blip = counter % 10;
  const brighest = [];
  let hl = {
      dist: 5000000,
      c: "",
      n: "",
  };
  for (const star of stars.values())
  {
      // const star = stars.get(n);
      const x = star.x;
      const y = star.y;
      let r = star.h - star.d / 10;
      if (brighest.length < 5)
      {
          brighest.push({r: r, c: star});
          brighest.sort((a, b) => a.r - b.r);
      }
      else if (r > brighest[0].r)
      {
          brighest[0] = {r: r, c: star};
          brighest.sort((a, b) => a.r - b.r);
      }
      let radius = 0.5;
      if (r > 1000)
      {
          radius = 2;
      }
      else if (r > 100)
      {
          radius = 1.5;
      }
      else if (r > 10) {
          radius = 1;
      }

      const dist = ((x - state.mouse[0]) * (x - state.mouse[0]) + (y - state.mouse[1]) * (y - state.mouse[1])) / radius;
      if (dist < hl.dist)
      {
            hl = {
                dist: dist,
                c: star.c,
                n: star.n,
                x: x,
                y: y,
            };
      }
      const opacity = ((cnt % 10 == blip) && (radius > 0.5)) ? 0.5 : 1; //getOpacity(counter * cnt);
      // fillCircle(ctx, x, y, radius, `rgba(255, 255, 255, ${opacity})`);
      fillCircle(ctx, x, y, radius, `rgba(${star.c},${opacity})`);
      cnt++;
  }

  for (let i = 0; i < brighest.length; i++)
  {
      const star = brighest[i].c;
      drawStar(ctx, star.x, star.y, star.c);
      // console.log("brightest:", i, star.n, brighest[i].r);
  }

  renderMoon(ctx, 0, ts);
  renderMeteors(ctx, 0);

  if (lastHL.n != hl.n)
    {
        document.getElementById("tooltip").innerHTML = hl.n;
        document.getElementById("tooltip").style.left = `${hl.x}px`;
        document.getElementById("tooltip").style.top = `${hl.y}px`;
        document.getElementById("tooltip").style.color = `rgb(${hl.c})`;
        lastHL = hl;
    }

  counter++;
  if (state.restart)
  {
      restart(ts);
  }
    else {
      requestAnimationFrame(render);
    }
}

const backgroundColor = "#030318";
const width = window.innerWidth;
const height = window.innerHeight;
const maxStarRadius = 1.5;
const minStarOpacity = 0.1;
const maxStarOpacity = 0.7;
const stars = initStars(); // createStars(width, height, 30);
const moon = {
  color: "#fea",
  x: height / 3,
  y: width / 3,
  r: 40
};

const canvas = document.querySelector("#canvas");
const ctx = canvas.getContext("2d");
canvas.width = width;
canvas.height = height;

let counter = 0;

let all_changes = [];

let state = {};
async function fetch_data()
{
    const urlParams = new URLSearchParams(window.location.search);
    const repoRoot = urlParams.get('repo');
    const resp = await fetch(repoRoot + '/index.json');
    console.log(resp);
    const data = await resp.json();
    window.document.getElementById("repo").innerHTML = data.name;
    for (const fname of data.data)
    {
        window.document.getElementById("progress").innerHTML = "Loading " + fname + "...";
        const resp = await fetch(repoRoot + '/' + fname);
        const data = await resp.json();
        console.log(data.length);
        all_changes = all_changes.concat(data);
    }
    window.document.getElementById("progress").innerHTML = "Starting...";
    return data;
}

const moonImage = document.getElementById("moon");
let moonReady = false;

if (moonImage.complete) {
    moonReady = true;
    console.log("complete");
} else{
    moonImage.addEventListener("load", () => {
        moonReady = true;
        console.log("loaded");
    });
}

function restart(ts) {
    state.lastTs = ts;
    state.stars = 0;
    state.nextChangeToProcess = 0;
    state.removeQueue = new Set();
    state.checkpoint = [ts, state.start];
    state.restart = false;
    state.message = "";
    state.highlight = ["", 5000000];
    state.commitsByAuthor = new Map();
    state.meteors = [];
    stars.clear();
    requestAnimationFrame(render);
}

fetch_data().then(data => {
    console.log(data);
    state = {
        lastTs: 0,
        start: new Date(),
        end: new Date(),
        nextChangeToProcess: 0,
        removeQueue: new Set(),
        stars: 0,
        checkpoint: [0, 0],
        restart: false,
        message: "",
        mouse: [0, 0],
        highlight: ["", 5000000],
        commitsByAuthor: new Map(),
        meteors: [],
    };
    state.start.setTime(Date.parse(data.start));
    state.checkpoint = [0, state.start];
    state.end.setTime(Date.parse(data.end));
    console.log(state);
    window.document.getElementById("progress").innerHTML = "Rendering...";
    window.document.getElementById("flash").classList.add("fadeOut");
    setInterval(() => {
        render(0);
    }, 2000);
});

function changeSpeed(delta) {
    var d = projectDate(state.lastTs);
    state.checkpoint = [state.lastTs, d];
    daysPerSecond = delta;
}

document.addEventListener("keydown", event => {
    const keyName = event.key;
    if (keyName == "0") {
        changeSpeed(0);
    } else if (keyName == "1") {
        changeSpeed(1);
    } else if (keyName == "2") {
        changeSpeed(7);
    } else if (keyName == "3") {
        changeSpeed(30);
    } else if (keyName == "h") {
        document.getElementById("help").classList.toggle("fadeIn");
    } else if (keyName == "r") {
        state.restart = true;
    }
});

document.onmousemove = (event) => {
    let x = event.clientX;
    let y = event.clientY;
    state.mouse = [x, y];
    // document.querySelector("#tooltip").style.left = `${x}px`;
    // document.querySelector("#tooltip").style.top = `${y}px`;
}
