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
  fillCircle(ctx, moon.x, moon.y, moon.r, moon.color);
  // render a smaller circle above the moon to give it that well-known moon-shape
  fillCircle(
    ctx,
    moon.x - moon.r / 3,
    moon.y - moon.r / 3,
    moon.r,
    backgroundColor
  );

  ctx.font = "30px Arial";
  ctx.fillStyle = "white";
  state.lastTs = ts;
  var diff = ts / 1000 * daysPerSecond;
  var curDate = new Date(state.start.getTime() + diff * 24 * 60 * 60 * 1000);
  ctx.fillText("Elapsed time: " + curDate.toISOString() + " " + Object.keys(stars).length, moon.x + 10, moon.y + 50);
}

function getOpacity(factor) {
  const opacityIncrement =
    (maxStarOpacity - minStarOpacity) * Math.abs(Math.sin(factor));
  const opacity = minStarOpacity + opacityIncrement;
  return opacity;
}

function render(elapsed) {
  ctx.fillStyle = backgroundColor;
  ctx.clearRect(0, 0, width, height);
  let cnt = 0;
  for (const n in stars)
  {
      const star = stars[n];
      const x = star.x;
      const y = star.y;
      const opacity = getOpacity(counter * cnt);
      fillCircle(ctx, x, y, star.r, `rgba(255, 255, 255, ${opacity}`);
      cnt++;
  }

  renderMoon(ctx, 0, elapsed);

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
    for (const fname of data.data)
    {
        const resp = await fetch(repoRoot + '/' + fname);
        const data = await resp.json();
        console.log(data.length);
        all_changes = all_changes.concat(data);
        if (Object.keys(stars).length < 5000)
        {
            for (const change of data)
            {
                for (const s of change.on)
                {
                      const star = {
                        x: s.x * width / 256 / 256,
                        y: s.y * height / 256 / 256,
                        r: Math.random() * maxStarRadius
                      };
                      if (Object.keys(stars).length < 5000)
                    {
                        const key = star.x.toString() + ":" + star.y.toString();
                        stars[key] = star;
                    }
                }
            }
        }
    }
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
    render(0);
});

