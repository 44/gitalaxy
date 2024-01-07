function randomInt(max) {
  return Math.floor(Math.random() * max);
}

const started = new Date();
var lastShown = 0;
const daysPerSecond = 30;

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
    return {};
}

function fillCircle(ctx, x, y, r, fillStyle) {
  ctx.beginPath();
  ctx.fillStyle = fillStyle;
  ctx.arc(x, y, r, 0, Math.PI * 2);
  ctx.fill();
}

function renderMoon(ctx, blur, ts) {
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
  var diff = ts / 1000 * daysPerSecond;
  var curDate = new Date(state.start.getTime() + diff * 24 * 60 * 60 * 1000);
  var cutoff = curDate.toISOString().substring(0, 10);
  // ctx.fillText("Now: " + cutoff + " " + Object.keys(stars).length, moon.x + 10, moon.y + 50);
  document.getElementById("status").innerHTML = "Now: " + cutoff + " " + Object.keys(stars).length;
}

function getOpacity(factor) {
  const opacityIncrement =
    (maxStarOpacity - minStarOpacity) * Math.abs(Math.sin(factor));
  const opacity = minStarOpacity + opacityIncrement;
  return opacity;
}

function projectDate(ts) {
    var diff = ts / 1000 * daysPerSecond;
    var curDate = new Date(state.start.getTime() + diff * 24 * 60 * 60 * 1000);
    return curDate;
}

function applyDecay(ts) {
    for (const n in stars)
    {
        const star = stars[n];
        const daysFromLastHit = (ts - star.l) / 1000 * daysPerSecond;
        if (daysFromLastHit < 30)
        {
            continue;
        }
        const daysFromLastDecay = Math.floor((ts - star.ld) / 1000 * daysPerSecond);
        if (daysFromLastDecay < 1)
        {
            continue;
        }
        star.d += daysFromLastDecay;
        star.ld = ts;

        if (star.d > star.h * 10)
        {
            delete stars[n];
        }
    }
}

function updateStars(ts) {
    var curDate = projectDate(ts);
    var lastDate = projectDate(state.lastTs);
    applyDecay(ts);

    /*
    let decayDiff = (ts - state.lastTs) / 1000 * daysPerSecond;
    let decay = decayDiff * 0.01;
    for (const n in stars)
    {
        const star = stars[n];
        const delay = (ts - star.l) / 1000 * daysPerSecond;
        if (delay < 30)
        {
            continue;
        }
        star.r -= decay;
        if (star.r < 0.001)
        {
            delete stars[n];
        }
    }
    */

    state.lastTs = ts;

    var cutoff = curDate.toISOString().substring(0, 10);
    for (let i = state.processed; i < all_changes.length; i++) {
        const change = all_changes[i];
        if (change.date > cutoff) {
            break;
        }
        state.processed = i;
        for (const s of change.on) {
            const key = s.x.toString() + ":" + s.y.toString();
            if (key in stars) {
                stars[key].r += 0.01;
                stars[key].l = ts;
                stars[key].h++;
                stars[key].ld = ts;
                if (stars[key].r > 3) {
                    stars[key].r = 3;
                }
            } else {
                const star = {
                    n: s.fname,
                    x: s.x * width / 256 / 256,
                    y: s.y * height / 256 / 256,
                    r: 1.0, // radius - should be calculated from the number of hits and decay
                    l: ts, // last hit
                    h: 1, // hits
                    d: 0, // decay
                    ld: ts, // last decay
                };
                stars[key] = star;
            }
        }
        for (const s of change.off) {
            const key = s.x.toString() + ":" + s.y.toString();
            if (key in stars) {
                delete stars[key];
            }
        }
    }
}

let max_hits = 0;

function render(ts) {
  updateStars(ts);
  ctx.fillStyle = backgroundColor;
  ctx.clearRect(0, 0, width, height);
  let cnt = 0;
  const blip = counter % 10;
  for (const n in stars)
  {
      const star = stars[n];
      const x = star.x;
      const y = star.y;
      const opacity = (cnt % 20 == blip) ? 0.5 : 1; //getOpacity(counter * cnt);
      let r = star.h - star.d / 10;
      if (r > max_hits)
      {
          max_hits = r;
          // console.log(max_hits, star.n);
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
      fillCircle(ctx, x, y, radius, `rgba(255, 255, 255, ${opacity})`);
      cnt++;
  }

  renderMoon(ctx, 0, ts);

  counter++;
  requestAnimationFrame(render);
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

fetch_data().then(data => {
    console.log(data);
    state = {
        lastTs: 0,
        start: new Date(),
        end: new Date(),
        processed: 0,
    };
    state.start.setTime(Date.parse(data.start));
    state.end.setTime(Date.parse(data.end));
    console.log(state);
    window.document.getElementById("progress").innerHTML = "Rendering...";
    window.document.getElementById("flash").classList.add("fadeOut");
    setInterval(() => {
        render(0);
    }, 2000);
});

