#!/bin/sh
cd /home/claude/web
{ cat src/a_head.html src/a2_css.html src/b_body.html src/b2_sections.html
  echo '<script>'
  cat src/c_math.js src/d1_data.js src/d1b_parts.js src/d2_build.js src/e_shaders.js src/e2_shaders.js src/f_render.js src/g_app.js src/g2_app.js
  echo '</script>'
  echo '</body>'
  echo '</html>'; } > index.html
wc -c index.html
