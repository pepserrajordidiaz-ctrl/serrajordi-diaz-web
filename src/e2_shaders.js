const VS_SKY = `#version 300 es
out vec2 vN;
void main(){vec2 p=vec2(float((gl_VertexID<<1)&2),float(gl_VertexID&2));vN=p*2.-1.;gl_Position=vec4(vN,1.,1.);}
`;
const FS_SKY = `#version 300 es
precision highp float;
in vec2 vN; uniform mat4 uInvVP; uniform vec3 uEye,uSunDir,uSunCol,uFogCol,uSkyCol; uniform float uExposure;
uniform vec4 uAxes; // world x axis and z axis expressed in (E,N)
out vec4 outC;
${GLSL_COMMON}
float gs(float a,float c,float w){float d=mod(a-c+540.,360.)-180.;return exp(-d*d/(2.*w*w));}
float ridge(float a){
 float e=.65+4.5*gs(a,7.,15.)+1.0*gs(a,12.,4.)+.8*gs(a,353.,5.)+1.7*gs(a,40.,14.);
 e+=1.7*gs(a,86.,11.)+2.2*gs(a,111.,13.)+1.9*gs(a,160.,22.)+1.3*gs(a,203.,17.)+1.0*gs(a,316.,20.);
 return e+.45*(vnoise(vec2(a*.33,1.))-.5)+.2*(vnoise(vec2(a*1.9,7.))-.5);
}
void main(){
 vec4 w=uInvVP*vec4(vN,1.,1.); vec3 d=normalize(w.xyz/w.w-uEye);
 float se=uSunDir.y, cs=dot(d,uSunDir);
 vec3 zen=mix(vec3(.035,.06,.14),vec3(.13,.30,.62),smoothstep(-.05,.35,se));
 vec3 hor=mix(vec3(.50,.38,.34),vec3(.70,.78,.86),smoothstep(0.,.45,se));
 hor=mix(hor,vec3(1.,.58,.30),(1.-smoothstep(0.,.3,se))*pow(max(cs,0.),3.)*.85);
 float h=d.y;
 vec3 c=mix(hor,zen,pow(clamp(h,0.,1.),.5));
 c+=uSunCol*(.05*pow(max(cs,0.),6.)+.22*pow(max(cs,0.),180.));
 c+=vec3(1.,.93,.82)*smoothstep(.99955,.9999,cs)*18.*step(-.02,h);
 if(h>0.){
  vec2 cu=d.xz/(h+.12);
  float n=fbm(cu*.42+vec2(3.1,7.7))*.7+fbm(cu*1.35+vec2(9.2,1.3))*.3;
  float dens=smoothstep(.5,.76,n)*smoothstep(.015,.2,h)*.82;
  vec3 hd=normalize(vec3(d.x,0.,d.z)+1e-4), sd=normalize(vec3(uSunDir.x,0.,uSunDir.z)+1e-4);
  float tw=dot(hd,sd)*.5+.5;
  vec3 cc=mix(uSkyCol*1.5+vec3(.26),vec3(.86,.86,.88),.55)*(.82+.18*smoothstep(.45,.8,n))+uSunCol*(.04+.13*tw*tw);
  c=mix(c,cc,dens);
 }
 float E=d.x*uAxes.x+d.z*uAxes.z, Nn=d.x*uAxes.y+d.z*uAxes.w;
 float az=mod(degrees(atan(E,Nn))+360.,360.), el=degrees(asin(clamp(h,-1.,1.)));
 float m=ridge(az);
 if(el<m&&el>-.6){
  vec3 mt=mix(vec3(.25,.30,.30),vec3(.36,.40,.42),smoothstep(1.,5.5,m))*(uSkyCol*1.1+.25);
  float t=clamp(el/max(m,.1),0.,1.);
  c=mix(mix(mt,uFogCol,.5),mt,t*.55);
  c=mix(c,hor,.25);
 }
 if(h<-.004)c=mix(c,uFogCol,smoothstep(-.004,-.03,h));
 outC=vec4(grade(c*uExposure),1.);
}
`;
const VS_DEPTH = `#version 300 es
layout(location=0) in vec3 aPos; layout(location=1) in vec3 aNrm; layout(location=2) in vec2 aUV; layout(location=4) in float aMat;
uniform mat4 uLVP; flat out float vMat; out vec2 vXZ; out vec2 vUV; out float vNy; out float vY;
void main(){vMat=aMat;vXZ=aPos.xz;vUV=aUV;vNy=aNrm.y;vY=aPos.y;gl_Position=uLVP*vec4(aPos,1.);}
`;
const FS_DEPTH = `#version 300 es
precision highp float; flat in float vMat; in vec2 vXZ; in vec2 vUV; in float vNy; in float vY; uniform vec4 uDisc; uniform float uClipH;
void main(){int m=int(vMat+.5); if(vY>uClipH)discard; if(m!=13&&m!=14&&length(vXZ-uDisc.xy)>uDisc.z)discard;
 if(m==16&&abs(vNy)<.5&&vUV.y>.07&&vUV.y<.88&&fract(vUV.x/.11)>.24)discard;}
`;
const FS_GHOST = `#version 300 es
precision highp float;
in vec3 vPos; in vec3 vNrm; in vec3 vCol; in vec2 vUV; in vec4 vL; flat in float vMat; flat in vec4 vP; flat in vec4 vQ;
uniform vec3 uSunDir; uniform float uAlpha, uGhostH, uDay; out vec4 outC;
void main(){
 if(vPos.y>uGhostH+.02)discard;
 vec3 N=normalize(vNrm);
 float e=min(min(vUV.x,vP.x-vUV.x),min(vUV.y,vP.y-vUV.y));
 float line=1.-smoothstep(.03,.075,e);
 float fl=0.; if(abs(N.y)<.5){fl=(1.-smoothstep(.025,.06,abs(vUV.y-3.2)))+(1.-smoothstep(.025,.06,abs(vUV.y-6.2)));}
 float k=max(line,fl*.8);
 vec3 c=mix(vec3(.97,.96,.93)*(.82+.18*max(dot(N,uSunDir),0.))*mix(.38,1.,uDay),vec3(.09,.12,.11),k);
 outC=vec4(c,(.26+.7*k)*uAlpha);
}
`;
