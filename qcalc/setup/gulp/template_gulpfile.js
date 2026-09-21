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
const projectRoot = 's:/PROJECTS/QCALC/github/qcalc_dock/qcalc';
const qcalc_TemplatesPath = `${projectRoot}/qsite/templates`;
const calcTemplatesPath = `${projectRoot}/calc/templates`;
const catalogTemplatesPath = `${projectRoot}/catalog/templates`;

gulp.task('include1', function() {
  return gulp.src([`${qcalc_TemplatesPath}/_gulp-base.html`])
    .pipe(fileinclude({
      prefix: '@@',
      basepath: '@file'
    }))
    .pipe(rename('gen-base.html'))
    .pipe(gulp.dest(qcalc_TemplatesPath));
});


gulp.task('include2a1', function() {
  return gulp.src([`${calcTemplatesPath}/_gulp-calculator-content-l2r.html`])
    .pipe(fileinclude({
      prefix: '@@',
      basepath: '@file'
    }))
    .pipe(rename('gen-calculator-content-l2r.html'))
    .pipe(gulp.dest(calcTemplatesPath));
});
gulp.task('include2a2', function() {
  return gulp.src([`${calcTemplatesPath}/_gulp-calculator-content-l2r2.html`])
    .pipe(fileinclude({
      prefix: '@@',
      basepath: '@file'
    }))
    .pipe(rename('gen-calculator-content-l2r2.html'))
    .pipe(gulp.dest(calcTemplatesPath));
});
gulp.task('include2a3', function() {
  return gulp.src([`${calcTemplatesPath}/_gulp-calculator-content-lr.html`])
    .pipe(fileinclude({
      prefix: '@@',
      basepath: '@file'
    }))
    .pipe(rename('gen-calculator-content-lr.html'))
    .pipe(gulp.dest(calcTemplatesPath));
});
gulp.task('include2a4', function() {
  return gulp.src([`${calcTemplatesPath}/_gulp-calculator-content-lr2.html`])
    .pipe(fileinclude({
      prefix: '@@',
      basepath: '@file'
    }))
    .pipe(rename('gen-calculator-content-lr2.html'))
    .pipe(gulp.dest(calcTemplatesPath));
});

gulp.task('include2a5', function() {
  return gulp.src([`${calcTemplatesPath}/_gulp-calculator-content-t2b.html`])
    .pipe(fileinclude({
      prefix: '@@',
      basepath: '@file'
    }))
    .pipe(rename('gen-calculator-content-t2b.html'))
    .pipe(gulp.dest(calcTemplatesPath));
});
gulp.task('include2a6', function() {
  return gulp.src([`${calcTemplatesPath}/_gulp-calculator-content-t2b2.html`])
    .pipe(fileinclude({
      prefix: '@@',
      basepath: '@file'
    }))
    .pipe(rename('gen-calculator-content-t2b2.html'))
    .pipe(gulp.dest(calcTemplatesPath));
});
gulp.task('include2a7', function() {
  return gulp.src([`${calcTemplatesPath}/_gulp-calculator-content-tb.html`])
    .pipe(fileinclude({
      prefix: '@@',
      basepath: '@file'
    }))
    .pipe(rename('gen-calculator-content-tb.html'))
    .pipe(gulp.dest(calcTemplatesPath));
});
gulp.task('include2a8', function() {
  return gulp.src([`${calcTemplatesPath}/_gulp-calculator-content-tb2.html`])
    .pipe(fileinclude({
      prefix: '@@',
      basepath: '@file'
    }))
    .pipe(rename('gen-calculator-content-tb2.html'))
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


gulp.task('include2c', function() {
  return gulp.src([`${calcTemplatesPath}/_gulp-calculator-partial.html`])
    .pipe(fileinclude({
      prefix: '@@',
      basepath: '@file'
    }))
    .pipe(rename('gen-calculator-partial.html'))
    .pipe(gulp.dest(calcTemplatesPath));
});

gulp.task('include2d', function() {
  return gulp.src([`${calcTemplatesPath}/_gulp-calculator-core.html`])
    .pipe(fileinclude({
      prefix: '@@',
      basepath: '@file'
    }))
    .pipe(rename('gen-calculator-core.html'))
    .pipe(gulp.dest(calcTemplatesPath));
});

gulp.task('include3a', function() {
  return gulp.src([`${catalogTemplatesPath}/_gulp-catalog-calc.html`])
    .pipe(fileinclude({
      prefix: '@@',
      basepath: '@file'
    }))
    .pipe(rename('gen-catalog-calc.html'))
    .pipe(gulp.dest(catalogTemplatesPath));
});

gulp.task('include3b', function() {
  return gulp.src([`${catalogTemplatesPath}/_gulp-catalog-qty.html`])
    .pipe(fileinclude({
      prefix: '@@',
      basepath: '@file'
    }))
    .pipe(rename('gen-catalog-qty.html'))
    .pipe(gulp.dest(catalogTemplatesPath));
});

gulp.task('include3c', function() {
  return gulp.src([`${catalogTemplatesPath}/_gulp-catalog-search.html`])
    .pipe(fileinclude({
      prefix: '@@',
      basepath: '@file'
    }))
    .pipe(rename('gen-catalog-search.html'))
    .pipe(gulp.dest(catalogTemplatesPath));
});

gulp.task('default', gulp.series('include1',  
	'include2a1', 'include2a2', 'include2a3', 'include2a4', 
	'include2a5', 'include2a6', 'include2a7', 'include2a8',
	'include2b', 'include2c', 'include2d', 
	'include3a', 'include3b', 'include3c')
);

