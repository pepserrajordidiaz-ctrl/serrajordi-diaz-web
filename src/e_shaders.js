// ---------- shaders ----------
const GLSL_COMMON = `
float h21(vec2 p){p=fract(p*vec2(123.34,456.21));p+=dot(p,p+45.32);return fract(p.x*p.y);}
float vnoise(vec2 p){vec2 i=floor(p),f=fract(p);f=f*f*(3.-2.*f);
 return mix(mix(h21(i),h21(i+vec2(1,0)),f.x),mix(h21(i+vec2(0,1)),h21(i+vec2(1,1)),f.x),f.y);}
float fbm(vec2 p){float s=0.,a=.5;for(int i=0;i<4;i++){s+=a*vnoise(p);p=p*2.03+17.1;a*=.5;}return s;}
vec3 aces(vec3 x){return clamp((x*(2.51*x+.03))/(x*(2.43*x+.59)+.14),0.,1.);}
vec3 grade(vec3 c){vec3 g=pow(aces(c),vec3(1./2.2)); g=mix(g,g*g*(3.-2.*g),.12);
 g=g*vec3(1.03,1.,.95)+vec3(.014,.01,.004); float l=dot(g,vec3(.299,.587,.114)); return mix(vec3(l),g,.97);}
`;
const VS_SCENE = `#version 300 es
layout(location=0) in vec3 aPos; layout(location=1) in vec3 aNrm; layout(location=2) in vec2 aUV;
layout(location=3) in vec3 aCol; layout(location=4) in float aMat; layout(location=5) in vec4 aP; layout(location=6) in vec4 aQ;
uniform mat4 uVP, uLVP;
out vec3 vPos; out vec3 vNrm; out vec3 vCol; out vec2 vUV; out vec4 vL;
flat out float vMat; flat out vec4 vP; flat out vec4 vQ;
void main(){vPos=aPos;vNrm=aNrm;vUV=aUV;vCol=aCol;vMat=aMat;vP=aP;vQ=aQ;vL=uLVP*vec4(aPos,1.);gl_Position=uVP*vec4(aPos,1.);}
`;
const FS_SCENE = `#version 300 es
precision highp float; precision highp sampler2DShadow;
in vec3 vPos; in vec3 vNrm; in vec3 vCol; in vec2 vUV; in vec4 vL;
flat in float vMat; flat in vec4 vP; flat in vec4 vQ;
uniform vec3 uEye, uSunDir, uSunCol, uSkyCol, uGndCol, uFogCol;
uniform float uFogDen, uExposure, uGlow, uLamp, uFocus;
uniform vec4 uDisc, uAOr; uniform vec2 uPoly[16]; uniform int uPolyN;
uniform sampler2DShadow uShadow; uniform sampler2D uAO;
out vec4 outC;
${GLSL_COMMON}
const vec2 PD[12]=vec2[12](vec2(-.326,-.406),vec2(-.840,-.074),vec2(-.696,.457),vec2(-.203,.621),vec2(.962,-.195),vec2(.473,-.480),
 vec2(.519,.767),vec2(.185,-.893),vec2(.507,.064),vec2(.896,.412),vec2(-.322,-.933),vec2(-.792,-.598));
float shadowAt(vec3 n){
 vec3 p=vL.xyz/vL.w*.5+.5;
 if(p.x<0.||p.x>1.||p.y<0.||p.y>1.||p.z>1.)return 1.;
 float ndl=max(dot(n,uSunDir),0.); float bias=.0004+.0016*(1.-ndl);
 vec2 ts=1./vec2(textureSize(uShadow,0)); float s=0., a=6.2832*h21(gl_FragCoord.xy*.37+.5);
 mat2 rot=mat2(cos(a),sin(a),-sin(a),cos(a));
 for(int i=0;i<12;i++)s+=texture(uShadow,vec3(p.xy+rot*PD[i]*ts*4.2,p.z-bias));
 return s/12.;
}
vec3 shutterCol(float s){return s<.5?vec3(.075,.14,.083):(s<1.5?vec3(.15,.085,.045):vec3(.60,.55,.45));}
vec3 facade(vec3 base,vec2 uv,bool front,out float glass,out float aoF,out float lampF){
 float gh=vP.x,fh=vP.y,fl=vP.z,bw=vP.w,shop=vQ.x,sh=vQ.y,seed=vQ.z,fg=floor(vQ.w/10.+.01),style=vQ.w-fg*10.;
 glass=0.; lampF=0.; float H=gh+(fl-1.)*fh;
 float bay=floor(uv.x/bw), bx=uv.x-bay*bw-bw*.5, r=h21(vec2(bay,seed));
 // mineral paint over render: broad tonal drift, trowel texture and fine grain
 vec3 col=base*(.86+.12*fbm(uv*.35+seed)+.06*fbm(uv*2.3+seed*1.7)+.035*(h21(floor(uv*80.))-.5));
 col*=1.-.09*smoothstep(.45,.85,fbm(uv*vec2(.6,.25)+seed*.3));
 // rain streaks under the cornice and under every sill
 float st=vnoise(vec2(uv.x*2.6+seed,uv.y*.35));
 col*=1.-.16*smoothstep(H-2.2,H-.3,uv.y)*st;
 // dirt and splash near the pavement
 col*=mix(.74,1.,smoothstep(.0,1.4,uv.y+.4*fbm(uv*3.)));
 // stone plinth with joints
 if(uv.y<.85){vec2 b=vec2(uv.x/.62+step(1.,mod(floor(uv.y/.28),2.))*.5,uv.y/.28);
  vec3 sb=fg>.5&&fg<1.5?vec3(.085,.08,.075):base*.62;
  col=sb*(.86+.22*h21(floor(b)+seed))*(.9+.15*fbm(uv*6.));
  if(min(fract(b.x),fract(b.y))<.05)col*=.72;}
 if(fg>1.5&&front&&uv.y<gh)col=vec3(.12,.12,.13)*(.7+.6*h21(floor(uv*55.)))*(.92+.1*fbm(uv*2.));
 // cornice band
 if(uv.y>H-.42&&uv.y<H-.12)col=base*1.04*(.92+.1*fbm(uv*4.)); if(uv.y>H-.5&&uv.y<H-.42)col*=.68;
 if(uv.y<gh){
  if(front&&shop>.5&&bay>0.){
   float wx=bw*.5-.28;
   bool shut=fg>1.5||h21(vec2(bay,seed+5.))<.55;
   if(abs(bx)<wx&&uv.y>(shut?.06:.55)&&uv.y<gh-.6){ if(shut){col=vec3(.56,.56,.53)*(.7+.3*smoothstep(.08,.5,fract(uv.y*9.)))*(.88+.16*fbm(uv*4.)); col=mix(col,vec3(.36,.2,.1),.5*smoothstep(.72,.86,fbm(uv*2.3+seed)));} else glass=1.;}
   else if(abs(bx)<wx+.07&&uv.y>.5&&uv.y<gh-.55)col=vec3(.045,.05,.05)*(.8+.4*fbm(uv*12.));
   if(uv.y>gh-.55&&uv.y<gh-.2&&abs(bx)<wx+.07)col=vec3(.07,.08,.08)+.05*r;
  }else if(front&&bay<.5){
   if(abs(bx)<.62&&uv.y<2.4){col=vec3(.17,.11,.065)*(.75+.3*fbm(vec2(uv.x*2.,uv.y*28.)))*(fract(bx*2.6)<.05?.65:1.);
    if(abs(bx-.42)<.03&&abs(uv.y-1.05)<.04)col=vec3(.5,.42,.25);}
   else if(abs(bx)<.75&&uv.y<2.55)col=base*.58;
  }else if(front&&r<.35&&shop<.5){
   if(abs(bx)<1.2&&uv.y<2.45)col=vec3(.28,.28,.27)*(.82+.18*smoothstep(.15,.5,fract(uv.y*7.)))*(.85+.25*fbm(uv*3.));
  }else{
   if(abs(bx)<.55&&uv.y>1.05&&uv.y<2.3){glass=1.; if(front&&fract(bx*4.5)<.1)glass=0.;}
  }
 }else{
  float f=floor((uv.y-gh)/fh), fy=uv.y-gh-f*fh;
  bool bal=front&&(style<.5||(style<1.5&&mod(bay,2.)<.5));
  float ww=style>1.5?2.0:(bal?1.1:1.3), y0=bal?.02:.95, y1=style>1.5?2.4:2.25;
  if(!front){ww=.95;y0=1.0;y1=2.15;}
  if(uv.y<H-.5){
   if(fg>1.5&&front&&abs(bx)<ww*.5+.55){vec2 k=vec2(uv.x/.29+step(1.,mod(floor(uv.y/.075),2.))*.5,uv.y/.075);
    col=vec3(.42,.15,.08)*(.78+.32*h21(floor(k)))*mix(min(fract(k.x),fract(k.y))<.13?.72:1.,1.,smoothstep(.3,.8,fwidth(k.y)));}
   if(abs(bx)<ww*.5&&fy>y0&&fy<y1){
    float cov=h21(vec2(bay*7.+f,seed+3.)); cov=(cov<.4||style>1.5)?0.:cov*.8;
    float wy=(fy-y0)/(y1-y0);
    if(wy>1.-cov){col=shutterCol(sh)*(.62+.38*smoothstep(.15,.55,fract(fy*15.)))*(.82+.3*fbm(uv*5.));}
    else glass=1.;
    if(style>1.5&&abs(bx)<.025){glass=0.;col=vec3(.06);}
    if(glass>.5&&style<1.5&&(abs(bx)<.025||abs(wy-.68)<.012)){glass=0.;col=vec3(.78,.77,.72);} 
    if(wy>1.-cov-.04&&wy<1.-cov&&cov>0.)col*=.45;
   }else if(abs(bx)<ww*.5+.08&&fy>y0-.08&&fy<y1+.1){
    col=style>1.5?vec3(.06):vec3(.80,.79,.74)*(.88+.15*fbm(uv*9.));
    if(fy>y1&&fy<y1+.1)col=base*.82;}
   if(!bal&&abs(bx)<ww*.5+.16&&fy>y0-.14&&fy<y0-.06)col=base*.8;
   if(abs(bx)<ww*.5+.1&&fy<y0-.14&&fy>y0-1.4)col*=1.-.12*(1.-smoothstep(y0-1.4,y0-.14,fy))*vnoise(vec2(uv.x*6.,seed));
   if(fy<.05)col*=.9;
  }
 }
 aoF=mix(.55,1.,smoothstep(0.,1.8,uv.y));
 if(glass>.5){
  float wr=h21(vec2(bay*3.1+floor(uv.y/2.95),seed+9.));
  vec3 inside=vec3(.016,.018,.021)*(.7+.6*wr);
  if(wr>.45&&abs(bx)>(1.-wr)*.5)inside=mix(vec3(.34,.30,.25),vec3(.36,.26,.22),step(.7,wr))*(.78+.22*sin(uv.x*38.))*.6;
  if(wr>.9)inside+=vec3(.10,.06,.025);
  lampF=step(.62,h21(vec2(bay*5.3+floor(uv.y/2.95),seed+21.)));
  col=inside;
 }
 return col;
}
void main(){
 int m=int(vMat+.5);
 if(m!=13&&m!=14&&length(vPos.xz-uDisc.xy)>uDisc.z)discard;
 vec3 N=normalize(vNrm);
 if(!gl_FrontFacing){
  if(m==11||m==21)N=-N;
  else{ vec3 cut=vec3(.62,.63,.6)*(.9+.1*N.y); outC=vec4(grade(cut*uExposure*.95),1.); return; }
 }
 vec3 V=normalize(uEye-vPos); vec3 alb=vCol; float ao=1., glass=0., spec=0., emis=0., lampF=0., lampE=0.;
 vec2 xz=vPos.xz;
 if(m==1||m==2){alb=facade(vCol,vUV,m==1,glass,ao,lampF);}
 else if(m==3){alb=vCol*(.78+.2*fbm(vUV*.5+vQ.x)+.08*fbm(vUV*3.))*(1.-.07*step(.5,fract(vUV.y/2.95+.1)));
  float pt=smoothstep(.58,.66,fbm(vUV*.22+vQ.x*.1));
  vec2 b=vec2(vUV.x/.29+step(1.,mod(floor(vUV.y/.075),2.))*.5,vUV.y/.075); float fw=fwidth(b.y);
  vec3 br=vec3(.40,.19,.11)*(.8+.35*h21(floor(b)))*mix(min(fract(b.x),fract(b.y))<.12?.7:1.,1.,smoothstep(.3,.8,fw));
  alb=mix(alb,br,pt*.9); alb*=1.-.15*vnoise(vec2(vUV.x*2.,vUV.y*.3))*smoothstep(2.,6.,vUV.y);
  ao=mix(.6,1.,smoothstep(0.,2.,vUV.y));}
 else if(m==4){vec2 t=vec2(vUV.x/.21,vUV.y/.38); vec2 id=floor(t);
  alb=vCol*(.78+.32*h21(id+vQ.x))*(.82+.18*abs(sin(t.x*3.1416)))*(fract(t.y)<.14?.72:1.);
  alb=mix(alb,vec3(.20,.20,.16),.25*smoothstep(.55,.8,fbm(vUV*.5+vQ.x)));}
 else if(m==5){ if(vCol.r>vCol.b*1.2){ vec2 t=vec2(xz.x/.22,xz.y/.42); t.x+=.5*step(1.,mod(floor(t.y),2.)); vec2 id=floor(t);
   alb=vec3(.40,.16,.08)*(.72+.45*h21(id+vQ.x))*(.78+.22*abs(sin(t.x*3.1416)))*(fract(t.y)<.16?.65:1.);
   alb=mix(alb,vec3(.16,.15,.10),.35*smoothstep(.5,.8,fbm(xz*.4+vQ.x)));}
  else { vec2 t=xz/.3; alb=mix(vCol,vec3(.42,.25,.16),step(.55,h21(vec2(vQ.x)))*.7)*(.82+.22*h21(floor(t)))*(min(fract(t.x),fract(t.y))<.06?.78:1.)*(1.-.15*smoothstep(.55,.8,fbm(xz*.3)));}}
 else if(m==6){alb=vCol*(.74+.34*fbm(xz*1.6))*(.94+.12*(h21(floor(xz*70.))-.5));
  float pa=fbm(floor(xz*.6)*.7+3.); if(pa>.6)alb*=.8;
  float cr=abs(vnoise(xz*.9+7.)-.5); alb*=mix(.8,1.,smoothstep(.004,.014,cr));
  alb*=1.-.18*smoothstep(.62,.8,fbm(xz*.5+11.)); spec=.03;}
 else if(m==7){vec2 t=xz/vec2(.3,.15); t.x+=.5*step(1.,mod(floor(t.y),2.)); vec2 q=fract(t); alb=vCol*(.82+.2*h21(floor(t)))*(min(q.x*2.,q.y)<.08?.72:1.);
  alb*=1.-.2*smoothstep(.55,.8,fbm(xz*.7+5.)); alb*=.92+.1*fbm(xz*3.); alb=mix(alb,vec3(.18,.17,.15),.6*step(.995,h21(floor(xz*9.))));}
 else if(m==8){alb=vCol*(.74+.4*fbm(xz*1.3))*(.86+.28*h21(floor(xz*25.)));
  float gr=smoothstep(.5,.7,fbm(xz*.9+2.));
  alb=mix(alb,mix(vec3(.19,.24,.08),vec3(.40,.35,.15),fbm(xz*3.1+1.)),.85*gr);
  vec2 fc=xz*4.2, fi=floor(fc); vec2 fo=vec2(h21(fi),h21(fi+3.7))-.5; float fdd=length(fract(fc)-.5-fo*.55);
  float hue=h21(fi+5.3), fl=(1.-smoothstep(.12,.17,fdd))*step(.55,h21(fi+9.1))*gr;
  alb=mix(alb,hue<.45?vec3(.90,.72,.16):(hue<.78?vec3(.93,.91,.86):vec3(.58,.42,.78)),fl);
  float d=1e9; for(int i=0;i<16;i++){ if(i>=uPolyN)break; int j=i+1==uPolyN?0:i+1; vec2 a=uPoly[i],ba=uPoly[j]-a,pa=xz-a; float h=clamp(dot(pa,ba)/dot(ba,ba),0.,1.); d=min(d,length(pa-ba*h)); }
  float band=1.-smoothstep(.13,.2,d); alb=mix(alb,vec3(.85,.48,.02),band); emis=band*uGlow;}
 else if(m==19){vec2 t=vec2(vUV.x/.4+.5*step(1.,mod(floor(vUV.y/.2),2.)),vUV.y/.2); alb=vCol*(.8+.22*h21(floor(t)+vQ.x))*(.88+.18*fbm(vUV*3.));
  if(min(fract(t.x)*2.,fract(t.y))<.06)alb*=.78; alb*=mix(.72,1.,smoothstep(0.,.9,vUV.y)); alb*=1.-.12*vnoise(vec2(vUV.x*3.,vUV.y*.4));}
 else if(m==20){alb=vCol*(.66+.34*smoothstep(.08,.45,fract(vUV.y*8.)))*(.85+.25*fbm(vUV*2.5)); spec=.1;}
 else if(m==18){alb=vCol*(.8+.25*fbm(vec2(xz.x+xz.y,vUV.y)*3.));}
 else if(m==23){float st=step(.5,fract((xz.x-xz.y)*2.2)); alb=mix(vCol,vec3(.93,.88,.82),st*.55);}
 else if(m==9){alb=mix(vCol,vec3(.32,.28,.14),.45*smoothstep(.45,.75,fbm(xz*.35)))*(.8+.35*fbm(xz*1.1));}
 else if(m==10){vec2 t=xz/.5; alb=vCol*(.88+.14*fbm(xz*.8))*(min(fract(t.x),fract(t.y))<.04?.85:1.);}
 else if(m==11){alb=vCol*(.7+.5*fbm(vPos.xz*1.6+vPos.y*1.3)); ao=.55+.45*(N.y*.5+.5);}
 else if(m==13){alb=vCol*(.85+.15*smoothstep(-1.6,.1,vPos.y));}
 else if(m==16){if(abs(N.y)<.5&&vUV.y>.07&&vUV.y<.88&&fract(vUV.x/.11)>.24)discard; spec=.25;}
 else if(m==22){lampE=uLamp*2.6;}
 if(m>=6&&m<=10){vec2 a=(xz-uAOr.xy)/uAOr.z; if(a.x>0.&&a.y>0.&&a.x<1.&&a.y<1.)ao*=mix(.42,1.,texture(uAO,a).r);}
 float ndl=max(dot(N,uSunDir),0.); if(m==11)ndl=max(dot(N,uSunDir)*.6+.4,0.);
 float sh=ndl>0.?shadowAt(N):0.;
 vec3 amb=mix(uGndCol,uSkyCol,N.y*.5+.5);
 vec3 c=alb*(uSunCol*ndl*sh+amb*ao);
 if(glass>.5||spec>0.){
  vec3 R=reflect(-V,N); float fr=.04+.96*pow(1.-max(dot(N,V),0.),5.);
  vec3 env=mix(uFogCol*1.05,uSkyCol*1.6,smoothstep(-.05,.5,R.y));
  float k=glass>.5?mix(.16,.85,fr):spec*fr;
  c+=env*k*(glass>.5?.9:1.)*mix(.6,1.,sh);
  c+=uSunCol*pow(max(dot(R,uSunDir),0.),220.)*sh*(glass>.5?4.:spec*6.);
 }
 c+=vec3(1.,.62,.08)*emis*1.4;
 c+=vec3(1.,.64,.32)*(lampF*glass*uLamp*1.5+lampE);
 { // focus on the plot: the surroundings fade into a soft, pale haze
  float fd=length(vPos.xz-vec2(.6,-.5)), f=smoothstep(9.,30.,fd)*uFocus*(m==13||m==14?0.:1.);
  float l=dot(c,vec3(.3,.59,.11));
  vec3 soft=mix(vec3(l),c,.35)*.42+vec3(.64,.62,.58)*.58;
  c=mix(c,soft,f*.84);
  float edge=(m==13||m==14)?1.:smoothstep(31.,43.5,fd);   // the model has no hard edge: it melts into the same haze
  c=mix(c,vec3(.62,.60,.56),edge);
 }
 float dist=length(vPos-uEye); float fog=1.-exp(-dist*uFogDen);
 vec3 fc=uFogCol+uSunCol*.07*pow(max(dot(-V,uSunDir),0.),8.);
 c=mix(c,fc,clamp(fog,0.,.55));
 vec3 g=grade(c*uExposure);
 outC=vec4(g+(h21(gl_FragCoord.xy*.731+3.1)-.5)*.018,1.);
}
`;
