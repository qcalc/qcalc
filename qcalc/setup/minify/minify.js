// Minifies qCalc's own CSS/JS in qsite/static and calc/static (vendor/ and *.min.* are skipped) into <name>.min.<ext> next to each source.
// Only sources newer than their .min file are rebuilt.
//   node minify.js          one pass
//   node minify.js --watch  one pass, then rebuild on every save
//   node minify.js --force  rebuild everything
const fs = require('fs')
const path = require('path')
const esbuild = require('esbuild')

const appRoot = path.resolve(__dirname, '../..')
// qedit is left out: its templates use plain {% static %}, so a .min file would never be served
const staticRoots = ['qsite', 'calc'].map(app => path.join(appRoot, app, 'static'))
const force = process.argv.includes('--force')

function* sources(dir) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name)
    if (e.isDirectory()) {
      if (e.name !== 'vendor') yield* sources(p)
    } else if (/\.(js|css)$/.test(e.name) && !/\.min\.(js|css)$/.test(e.name)) {
      yield p
    }
  }
}

function minify(file) {
  const out = file.replace(/\.(js|css)$/, '.min.$1')
  if (!force && fs.existsSync(out) && fs.statSync(out).mtimeMs >= fs.statSync(file).mtimeMs) return
  try {
    esbuild.buildSync({ entryPoints: [file], outfile: out, minify: true, legalComments: 'none', logLevel: 'warning' })
    const kb = n => (fs.statSync(n).size / 1024).toFixed(1)
    console.log(`${path.relative(appRoot, file)}: ${kb(file)} KB -> ${kb(out)} KB`)
  } catch (e) {
    console.error(`FAILED ${file}`)
  }
}

for (const root of staticRoots) for (const f of sources(root)) minify(f)

if (process.argv.includes('--watch')) {
  console.log('watching for changes (Ctrl+C to stop)')
  const timers = {}
  for (const root of staticRoots) {
    fs.watch(root, { recursive: true }, (_, name) => {
      if (!name || name.startsWith('vendor') || /\.min\.(js|css)$/.test(name) || !/\.(js|css)$/.test(name)) return
      const file = path.join(root, name)
      clearTimeout(timers[file])
      timers[file] = setTimeout(() => fs.existsSync(file) && minify(file), 200)
    })
  }
}
