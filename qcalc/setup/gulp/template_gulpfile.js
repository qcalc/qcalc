// Gulp file for compiling template partials into generated HTML files
// Install node.js on windows
// Install gulp
// > npm install --global gulp-cli
// Install sass
// > npm install -g sass
// Then run the following batch file from your project root qcalc_dock/qcalc
// > setup/run_sass.bat

var fileinclude = require('gulp-file-include');
const gulp = require('gulp');
const rename = require('gulp-rename');

// Replace this path with your own project path
const appRoot = '<replace_your_path>/qcalc_dock/qcalc';
const qcalc_TemplatesPath = `${appRoot}/qsite/templates`;
const calcTemplatesPath = `${appRoot}/calc/templates`;
const catalogTemplatesPath = `${appRoot}/catalog/templates`;

gulp.task('include1', function() {
  return gulp.src([`${qcalc_TemplatesPath}/_gulp-base.html`])
    .pipe(fileinclude({
      prefix: '@@',
      basepath: '@file'
    }))
    .pipe(rename('gen-base.html'))
    .pipe(gulp.dest(qcalc_TemplatesPath));
});

gulp.task('include2a', function() {
  return gulp.src([`${calcTemplatesPath}/_gulp-calculator-content-v4.27.html`])
    .pipe(fileinclude({
      prefix: '@@',
      basepath: '@file'
    }))
    .pipe(rename('gen-calculator-content-v4.27.html'))
    .pipe(gulp.dest(calcTemplatesPath));
});

gulp.task('include2b', function() {
  return gulp.src([`${calcTemplatesPath}/_gulp-calculator.html`])
    .pipe(fileinclude({
      prefix: '@@',
      basepath: '@file'
    }))
    .pipe(rename('gen-calculator.html'))
    .pipe(gulp.dest(calcTemplatesPath));
});

gulp.task('include3', function() {
  return gulp.src([`${calcTemplatesPath}/_gulp-calculator-partial.html`])
    .pipe(fileinclude({
      prefix: '@@',
      basepath: '@file'
    }))
    .pipe(rename('gen-calculator-partial.html'))
    .pipe(gulp.dest(calcTemplatesPath));
});

gulp.task('include4', function() {
  return gulp.src([`${calcTemplatesPath}/_gulp-calculator-core.html`])
    .pipe(fileinclude({
      prefix: '@@',
      basepath: '@file'
    }))
    .pipe(rename('gen-calculator-core.html'))
    .pipe(gulp.dest(calcTemplatesPath));
});

gulp.task('include5', function() {
  return gulp.src([`${catalogTemplatesPath}/_gulp-catalog-calc.html`])
    .pipe(fileinclude({
      prefix: '@@',
      basepath: '@file'
    }))
    .pipe(rename('gen-catalog-calc.html'))
    .pipe(gulp.dest(catalogTemplatesPath));
});

gulp.task('include6', function() {
  return gulp.src([`${catalogTemplatesPath}/_gulp-catalog-qty.html`])
    .pipe(fileinclude({
      prefix: '@@',
      basepath: '@file'
    }))
    .pipe(rename('gen-catalog-qty.html'))
    .pipe(gulp.dest(catalogTemplatesPath));
});

gulp.task('include7', function() {
  return gulp.src([`${catalogTemplatesPath}/_gulp-catalog-search.html`])
    .pipe(fileinclude({
      prefix: '@@',
      basepath: '@file'
    }))
    .pipe(rename('gen-catalog-search.html'))
    .pipe(gulp.dest(catalogTemplatesPath));
});

gulp.task('default', gulp.series('include1', 'include2a', 'include2b', 'include3',
	'include4', 'include5', 'include6', 'include7'));

