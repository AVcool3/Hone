import{i as $r,j as L,k as Kr,L as Ai,D as tn,u as Gr,l as Yr,m as Qr,r as Qe,n as Xr,d as Ln,N as Jr,a as vn}from"./index-dPu5jijA.js";function Zr(e,n){const t={};return(e[e.length-1]===""?[...e,""]:e).join((t.padRight?" ":"")+","+(t.padLeft===!1?"":" ")).trim()}const e0=/^[$_\p{ID_Start}][$_\u{200C}\u{200D}\p{ID_Continue}]*$/u,n0=/^[$_\p{ID_Start}][-$_\u{200C}\u{200D}\p{ID_Continue}]*$/u,t0={};function Et(e,n){return(t0.jsx?n0:e0).test(e)}const i0=/[ \t\n\f\r]/g;function r0(e){return typeof e=="object"?e.type==="text"?St(e.value):!1:St(e)}function St(e){return e.replace(i0,"")===""}class Ke{constructor(n,t,i){this.normal=t,this.property=n,i&&(this.space=i)}}Ke.prototype.normal={};Ke.prototype.property={};Ke.prototype.space=void 0;function Ci(e,n){const t={},i={};for(const r of e)Object.assign(t,r.property),Object.assign(i,r.normal);return new Ke(t,i,n)}function On(e){return e.toLowerCase()}class ie{constructor(n,t){this.attribute=t,this.property=n}}ie.prototype.attribute="";ie.prototype.booleanish=!1;ie.prototype.boolean=!1;ie.prototype.commaOrSpaceSeparated=!1;ie.prototype.commaSeparated=!1;ie.prototype.defined=!1;ie.prototype.mustUseProperty=!1;ie.prototype.number=!1;ie.prototype.overloadedBoolean=!1;ie.prototype.property="";ie.prototype.spaceSeparated=!1;ie.prototype.space=void 0;let o0=0;const q=Fe(),K=Fe(),Mn=Fe(),A=Fe(),j=Fe(),Ae=Fe(),oe=Fe();function Fe(){return 2**++o0}const Nn=Object.freeze(Object.defineProperty({__proto__:null,boolean:q,booleanish:K,commaOrSpaceSeparated:oe,commaSeparated:Ae,number:A,overloadedBoolean:Mn,spaceSeparated:j},Symbol.toStringTag,{value:"Module"})),Dn=Object.keys(Nn);class Zn extends ie{constructor(n,t,i,r){let a=-1;if(super(n,t),Tt(this,"space",r),typeof i=="number")for(;++a<Dn.length;){const o=Dn[a];Tt(this,Dn[a],(i&Nn[o])===Nn[o])}}}Zn.prototype.defined=!0;function Tt(e,n,t){t&&(e[n]=t)}function Re(e){const n={},t={};for(const[i,r]of Object.entries(e.properties)){const a=new Zn(i,e.transform(e.attributes||{},i),r,e.space);e.mustUseProperty&&e.mustUseProperty.includes(i)&&(a.mustUseProperty=!0),n[i]=a,t[On(i)]=i,t[On(a.attribute)]=i}return new Ke(n,t,e.space)}const Fi=Re({properties:{ariaActiveDescendant:null,ariaAtomic:K,ariaAutoComplete:null,ariaBusy:K,ariaChecked:K,ariaColCount:A,ariaColIndex:A,ariaColSpan:A,ariaControls:j,ariaCurrent:null,ariaDescribedBy:j,ariaDetails:null,ariaDisabled:K,ariaDropEffect:j,ariaErrorMessage:null,ariaExpanded:K,ariaFlowTo:j,ariaGrabbed:K,ariaHasPopup:null,ariaHidden:K,ariaInvalid:null,ariaKeyShortcuts:null,ariaLabel:null,ariaLabelledBy:j,ariaLevel:A,ariaLive:null,ariaModal:K,ariaMultiLine:K,ariaMultiSelectable:K,ariaOrientation:null,ariaOwns:j,ariaPlaceholder:null,ariaPosInSet:A,ariaPressed:K,ariaReadOnly:K,ariaRelevant:null,ariaRequired:K,ariaRoleDescription:j,ariaRowCount:A,ariaRowIndex:A,ariaRowSpan:A,ariaSelected:K,ariaSetSize:A,ariaSort:null,ariaValueMax:A,ariaValueMin:A,ariaValueNow:A,ariaValueText:null,role:null},transform(e,n){return n==="role"?n:"aria-"+n.slice(4).toLowerCase()}});function Ei(e,n){return n in e?e[n]:n}function Si(e,n){return Ei(e,n.toLowerCase())}const a0=Re({attributes:{acceptcharset:"accept-charset",classname:"class",htmlfor:"for",httpequiv:"http-equiv"},mustUseProperty:["checked","multiple","muted","selected"],properties:{abbr:null,accept:Ae,acceptCharset:j,accessKey:j,action:null,allow:null,allowFullScreen:q,allowPaymentRequest:q,allowUserMedia:q,alpha:q,alt:null,as:null,async:q,autoCapitalize:null,autoComplete:j,autoFocus:q,autoPlay:q,blocking:j,capture:null,charSet:null,checked:q,cite:null,className:j,closedBy:null,colorSpace:null,cols:A,colSpan:A,command:null,commandFor:null,content:null,contentEditable:K,controls:q,controlsList:j,coords:A|Ae,crossOrigin:null,data:null,dateTime:null,decoding:null,default:q,defer:q,dir:null,dirName:null,disabled:q,download:Mn,draggable:K,encType:null,enterKeyHint:null,fetchPriority:null,form:null,formAction:null,formEncType:null,formMethod:null,formNoValidate:q,formTarget:null,headers:j,height:A,hidden:Mn,high:A,href:null,hrefLang:null,htmlFor:j,httpEquiv:j,id:null,imageSizes:null,imageSrcSet:null,inert:q,inputMode:null,integrity:null,is:null,isMap:q,itemId:null,itemProp:j,itemRef:j,itemScope:q,itemType:j,kind:null,label:null,lang:null,language:null,list:null,loading:null,loop:q,low:A,manifest:null,max:null,maxLength:A,media:null,method:null,min:null,minLength:A,multiple:q,muted:q,name:null,nonce:null,noModule:q,noValidate:q,onAbort:null,onAfterPrint:null,onAuxClick:null,onBeforeMatch:null,onBeforePrint:null,onBeforeToggle:null,onBeforeUnload:null,onBlur:null,onCancel:null,onCanPlay:null,onCanPlayThrough:null,onChange:null,onClick:null,onClose:null,onContextLost:null,onContextMenu:null,onContextRestored:null,onCopy:null,onCueChange:null,onCut:null,onDblClick:null,onDrag:null,onDragEnd:null,onDragEnter:null,onDragExit:null,onDragLeave:null,onDragOver:null,onDragStart:null,onDrop:null,onDurationChange:null,onEmptied:null,onEnded:null,onError:null,onFocus:null,onFormData:null,onHashChange:null,onInput:null,onInvalid:null,onKeyDown:null,onKeyPress:null,onKeyUp:null,onLanguageChange:null,onLoad:null,onLoadedData:null,onLoadedMetadata:null,onLoadEnd:null,onLoadStart:null,onMessage:null,onMessageError:null,onMouseDown:null,onMouseEnter:null,onMouseLeave:null,onMouseMove:null,onMouseOut:null,onMouseOver:null,onMouseUp:null,onOffline:null,onOnline:null,onPageHide:null,onPageShow:null,onPaste:null,onPause:null,onPlay:null,onPlaying:null,onPopState:null,onProgress:null,onRateChange:null,onRejectionHandled:null,onReset:null,onResize:null,onScroll:null,onScrollEnd:null,onSecurityPolicyViolation:null,onSeeked:null,onSeeking:null,onSelect:null,onSlotChange:null,onStalled:null,onStorage:null,onSubmit:null,onSuspend:null,onTimeUpdate:null,onToggle:null,onUnhandledRejection:null,onUnload:null,onVolumeChange:null,onWaiting:null,onWheel:null,open:q,optimum:A,pattern:null,ping:j,placeholder:null,playsInline:q,popover:null,popoverTarget:null,popoverTargetAction:null,poster:null,preload:null,readOnly:q,referrerPolicy:null,rel:j,required:q,reversed:q,rows:A,rowSpan:A,sandbox:j,scope:null,scoped:q,seamless:q,selected:q,shadowRootClonable:q,shadowRootCustomElementRegistry:q,shadowRootDelegatesFocus:q,shadowRootMode:null,shadowRootSerializable:q,shape:null,size:A,sizes:null,slot:null,span:A,spellCheck:K,src:null,srcDoc:null,srcLang:null,srcSet:null,start:A,step:null,style:null,tabIndex:A,target:null,title:null,translate:null,type:null,typeMustMatch:q,useMap:null,value:K,width:A,wrap:null,writingSuggestions:null,align:null,aLink:null,archive:j,axis:null,background:null,bgColor:null,border:A,borderColor:null,bottomMargin:A,cellPadding:null,cellSpacing:null,char:null,charOff:null,classId:null,clear:null,code:null,codeBase:null,codeType:null,color:null,compact:q,declare:q,event:null,face:null,frame:null,frameBorder:null,hSpace:A,leftMargin:A,link:null,longDesc:null,lowSrc:null,marginHeight:A,marginWidth:A,noResize:q,noHref:q,noShade:q,noWrap:q,object:null,profile:null,prompt:null,rev:null,rightMargin:A,rules:null,scheme:null,scrolling:K,standby:null,summary:null,text:null,topMargin:A,valueType:null,version:null,vAlign:null,vLink:null,vSpace:A,allowTransparency:null,autoCorrect:null,autoSave:null,credentialless:q,disablePictureInPicture:q,disableRemotePlayback:q,exportParts:Ae,part:j,prefix:null,property:null,results:A,security:null,unselectable:null},space:"html",transform:Si}),s0=Re({attributes:{accentHeight:"accent-height",alignmentBaseline:"alignment-baseline",arabicForm:"arabic-form",baselineShift:"baseline-shift",capHeight:"cap-height",className:"class",clipPath:"clip-path",clipRule:"clip-rule",colorInterpolation:"color-interpolation",colorInterpolationFilters:"color-interpolation-filters",colorProfile:"color-profile",colorRendering:"color-rendering",crossOrigin:"crossorigin",dataType:"datatype",dominantBaseline:"dominant-baseline",enableBackground:"enable-background",fillOpacity:"fill-opacity",fillRule:"fill-rule",floodColor:"flood-color",floodOpacity:"flood-opacity",fontFamily:"font-family",fontSize:"font-size",fontSizeAdjust:"font-size-adjust",fontStretch:"font-stretch",fontStyle:"font-style",fontVariant:"font-variant",fontWeight:"font-weight",glyphName:"glyph-name",glyphOrientationHorizontal:"glyph-orientation-horizontal",glyphOrientationVertical:"glyph-orientation-vertical",hrefLang:"hreflang",horizAdvX:"horiz-adv-x",horizOriginX:"horiz-origin-x",horizOriginY:"horiz-origin-y",imageRendering:"image-rendering",letterSpacing:"letter-spacing",lightingColor:"lighting-color",markerEnd:"marker-end",markerMid:"marker-mid",markerStart:"marker-start",maskType:"mask-type",navDown:"nav-down",navDownLeft:"nav-down-left",navDownRight:"nav-down-right",navLeft:"nav-left",navNext:"nav-next",navPrev:"nav-prev",navRight:"nav-right",navUp:"nav-up",navUpLeft:"nav-up-left",navUpRight:"nav-up-right",onAbort:"onabort",onActivate:"onactivate",onAfterPrint:"onafterprint",onBeforePrint:"onbeforeprint",onBegin:"onbegin",onCancel:"oncancel",onCanPlay:"oncanplay",onCanPlayThrough:"oncanplaythrough",onChange:"onchange",onClick:"onclick",onClose:"onclose",onCopy:"oncopy",onCueChange:"oncuechange",onCut:"oncut",onDblClick:"ondblclick",onDrag:"ondrag",onDragEnd:"ondragend",onDragEnter:"ondragenter",onDragExit:"ondragexit",onDragLeave:"ondragleave",onDragOver:"ondragover",onDragStart:"ondragstart",onDrop:"ondrop",onDurationChange:"ondurationchange",onEmptied:"onemptied",onEnd:"onend",onEnded:"onended",onError:"onerror",onFocus:"onfocus",onFocusIn:"onfocusin",onFocusOut:"onfocusout",onHashChange:"onhashchange",onInput:"oninput",onInvalid:"oninvalid",onKeyDown:"onkeydown",onKeyPress:"onkeypress",onKeyUp:"onkeyup",onLoad:"onload",onLoadedData:"onloadeddata",onLoadedMetadata:"onloadedmetadata",onLoadStart:"onloadstart",onMessage:"onmessage",onMouseDown:"onmousedown",onMouseEnter:"onmouseenter",onMouseLeave:"onmouseleave",onMouseMove:"onmousemove",onMouseOut:"onmouseout",onMouseOver:"onmouseover",onMouseUp:"onmouseup",onMouseWheel:"onmousewheel",onOffline:"onoffline",onOnline:"ononline",onPageHide:"onpagehide",onPageShow:"onpageshow",onPaste:"onpaste",onPause:"onpause",onPlay:"onplay",onPlaying:"onplaying",onPopState:"onpopstate",onProgress:"onprogress",onRateChange:"onratechange",onRepeat:"onrepeat",onReset:"onreset",onResize:"onresize",onScroll:"onscroll",onSeeked:"onseeked",onSeeking:"onseeking",onSelect:"onselect",onShow:"onshow",onStalled:"onstalled",onStorage:"onstorage",onSubmit:"onsubmit",onSuspend:"onsuspend",onTimeUpdate:"ontimeupdate",onToggle:"ontoggle",onUnload:"onunload",onVolumeChange:"onvolumechange",onWaiting:"onwaiting",onZoom:"onzoom",overlinePosition:"overline-position",overlineThickness:"overline-thickness",paintOrder:"paint-order",panose1:"panose-1",pointerEvents:"pointer-events",referrerPolicy:"referrerpolicy",renderingIntent:"rendering-intent",shapeRendering:"shape-rendering",stopColor:"stop-color",stopOpacity:"stop-opacity",strikethroughPosition:"strikethrough-position",strikethroughThickness:"strikethrough-thickness",strokeDashArray:"stroke-dasharray",strokeDashOffset:"stroke-dashoffset",strokeLineCap:"stroke-linecap",strokeLineJoin:"stroke-linejoin",strokeMiterLimit:"stroke-miterlimit",strokeOpacity:"stroke-opacity",strokeWidth:"stroke-width",tabIndex:"tabindex",textAnchor:"text-anchor",textDecoration:"text-decoration",textRendering:"text-rendering",transformOrigin:"transform-origin",typeOf:"typeof",underlinePosition:"underline-position",underlineThickness:"underline-thickness",unicodeBidi:"unicode-bidi",unicodeRange:"unicode-range",unitsPerEm:"units-per-em",vAlphabetic:"v-alphabetic",vHanging:"v-hanging",vIdeographic:"v-ideographic",vMathematical:"v-mathematical",vectorEffect:"vector-effect",vertAdvY:"vert-adv-y",vertOriginX:"vert-origin-x",vertOriginY:"vert-origin-y",wordSpacing:"word-spacing",writingMode:"writing-mode",xHeight:"x-height",playbackOrder:"playbackorder",timelineBegin:"timelinebegin"},properties:{about:oe,accentHeight:A,accumulate:null,additive:null,alignmentBaseline:null,alphabetic:A,amplitude:A,arabicForm:null,ascent:A,attributeName:null,attributeType:null,azimuth:A,bandwidth:null,baselineShift:null,baseFrequency:null,baseProfile:null,bbox:null,begin:null,bias:A,by:null,calcMode:null,capHeight:A,className:j,clip:null,clipPath:null,clipPathUnits:null,clipRule:null,color:null,colorInterpolation:null,colorInterpolationFilters:null,colorProfile:null,colorRendering:null,content:null,contentScriptType:null,contentStyleType:null,crossOrigin:null,cursor:null,cx:null,cy:null,d:null,dataType:null,defaultAction:null,descent:A,diffuseConstant:A,direction:null,display:null,dur:null,divisor:A,dominantBaseline:null,download:q,dx:null,dy:null,edgeMode:null,editable:null,elevation:A,enableBackground:null,end:null,event:null,exponent:A,externalResourcesRequired:null,fill:null,fillOpacity:A,fillRule:null,filter:null,filterRes:null,filterUnits:null,floodColor:null,floodOpacity:null,focusable:null,focusHighlight:null,fontFamily:null,fontSize:null,fontSizeAdjust:null,fontStretch:null,fontStyle:null,fontVariant:null,fontWeight:null,format:null,fr:null,from:null,fx:null,fy:null,g1:Ae,g2:Ae,glyphName:Ae,glyphOrientationHorizontal:null,glyphOrientationVertical:null,glyphRef:null,gradientTransform:null,gradientUnits:null,handler:null,hanging:A,hatchContentUnits:null,hatchUnits:null,height:null,href:null,hrefLang:null,horizAdvX:A,horizOriginX:A,horizOriginY:A,id:null,ideographic:A,imageRendering:null,initialVisibility:null,in:null,in2:null,intercept:A,k:A,k1:A,k2:A,k3:A,k4:A,kernelMatrix:oe,kernelUnitLength:null,keyPoints:null,keySplines:null,keyTimes:null,kerning:null,lang:null,lengthAdjust:null,letterSpacing:null,lightingColor:null,limitingConeAngle:A,local:null,markerEnd:null,markerMid:null,markerStart:null,markerHeight:null,markerUnits:null,markerWidth:null,mask:null,maskContentUnits:null,maskType:null,maskUnits:null,mathematical:null,max:null,media:null,mediaCharacterEncoding:null,mediaContentEncodings:null,mediaSize:A,mediaTime:null,method:null,min:null,mode:null,name:null,navDown:null,navDownLeft:null,navDownRight:null,navLeft:null,navNext:null,navPrev:null,navRight:null,navUp:null,navUpLeft:null,navUpRight:null,numOctaves:null,observer:null,offset:null,onAbort:null,onActivate:null,onAfterPrint:null,onBeforePrint:null,onBegin:null,onCancel:null,onCanPlay:null,onCanPlayThrough:null,onChange:null,onClick:null,onClose:null,onCopy:null,onCueChange:null,onCut:null,onDblClick:null,onDrag:null,onDragEnd:null,onDragEnter:null,onDragExit:null,onDragLeave:null,onDragOver:null,onDragStart:null,onDrop:null,onDurationChange:null,onEmptied:null,onEnd:null,onEnded:null,onError:null,onFocus:null,onFocusIn:null,onFocusOut:null,onHashChange:null,onInput:null,onInvalid:null,onKeyDown:null,onKeyPress:null,onKeyUp:null,onLoad:null,onLoadedData:null,onLoadedMetadata:null,onLoadStart:null,onMessage:null,onMouseDown:null,onMouseEnter:null,onMouseLeave:null,onMouseMove:null,onMouseOut:null,onMouseOver:null,onMouseUp:null,onMouseWheel:null,onOffline:null,onOnline:null,onPageHide:null,onPageShow:null,onPaste:null,onPause:null,onPlay:null,onPlaying:null,onPopState:null,onProgress:null,onRateChange:null,onRepeat:null,onReset:null,onResize:null,onScroll:null,onSeeked:null,onSeeking:null,onSelect:null,onShow:null,onStalled:null,onStorage:null,onSubmit:null,onSuspend:null,onTimeUpdate:null,onToggle:null,onUnload:null,onVolumeChange:null,onWaiting:null,onZoom:null,opacity:null,operator:null,order:null,orient:null,orientation:null,origin:null,overflow:null,overlay:null,overlinePosition:A,overlineThickness:A,paintOrder:null,panose1:null,path:null,pathLength:A,patternContentUnits:null,patternTransform:null,patternUnits:null,phase:null,ping:j,pitch:null,playbackOrder:null,pointerEvents:null,points:null,pointsAtX:A,pointsAtY:A,pointsAtZ:A,preserveAlpha:null,preserveAspectRatio:null,primitiveUnits:null,propagate:null,property:oe,r:null,radius:null,referrerPolicy:null,refX:null,refY:null,rel:oe,rev:oe,renderingIntent:null,repeatCount:null,repeatDur:null,requiredExtensions:oe,requiredFeatures:oe,requiredFonts:oe,requiredFormats:oe,resource:null,restart:null,result:null,rotate:null,rx:null,ry:null,scale:null,seed:null,shapeRendering:null,side:null,slope:null,snapshotTime:null,specularConstant:A,specularExponent:A,spreadMethod:null,spacing:null,startOffset:null,stdDeviation:null,stemh:null,stemv:null,stitchTiles:null,stopColor:null,stopOpacity:null,strikethroughPosition:A,strikethroughThickness:A,string:null,stroke:null,strokeDashArray:oe,strokeDashOffset:null,strokeLineCap:null,strokeLineJoin:null,strokeMiterLimit:A,strokeOpacity:A,strokeWidth:null,style:null,surfaceScale:A,syncBehavior:null,syncBehaviorDefault:null,syncMaster:null,syncTolerance:null,syncToleranceDefault:null,systemLanguage:oe,tabIndex:A,tableValues:null,target:null,targetX:A,targetY:A,textAnchor:null,textDecoration:null,textRendering:null,textLength:null,timelineBegin:null,title:null,transformBehavior:null,type:null,typeOf:oe,to:null,transform:null,transformOrigin:null,u1:null,u2:null,underlinePosition:A,underlineThickness:A,unicode:null,unicodeBidi:null,unicodeRange:null,unitsPerEm:A,values:null,vAlphabetic:A,vMathematical:A,vectorEffect:null,vHanging:A,vIdeographic:A,version:null,vertAdvY:A,vertOriginX:A,vertOriginY:A,viewBox:null,viewTarget:null,visibility:null,width:null,widths:null,wordSpacing:null,writingMode:null,x:null,x1:null,x2:null,xChannelSelector:null,xHeight:A,y:null,y1:null,y2:null,yChannelSelector:null,z:null,zoomAndPan:null},space:"svg",transform:Ei}),Ti=Re({properties:{xLinkActuate:null,xLinkArcRole:null,xLinkHref:null,xLinkRole:null,xLinkShow:null,xLinkTitle:null,xLinkType:null},space:"xlink",transform(e,n){return"xlink:"+n.slice(5).toLowerCase()}}),Ii=Re({attributes:{xmlnsxlink:"xmlns:xlink"},properties:{xmlnsXLink:null,xmlns:null},space:"xmlns",transform:Si}),Bi=Re({properties:{xmlBase:null,xmlLang:null,xmlSpace:null},space:"xml",transform(e,n){return"xml:"+n.slice(3).toLowerCase()}}),l0={classId:"classID",dataType:"datatype",itemId:"itemID",strokeDashArray:"strokeDasharray",strokeDashOffset:"strokeDashoffset",strokeLineCap:"strokeLinecap",strokeLineJoin:"strokeLinejoin",strokeMiterLimit:"strokeMiterlimit",typeOf:"typeof",xLinkActuate:"xlinkActuate",xLinkArcRole:"xlinkArcrole",xLinkHref:"xlinkHref",xLinkRole:"xlinkRole",xLinkShow:"xlinkShow",xLinkTitle:"xlinkTitle",xLinkType:"xlinkType",xmlnsXLink:"xmlnsXlink"},u0=/[A-Z]/g,It=/-[a-z]/g,c0=/^data[-\w.:]+$/i;function h0(e,n){const t=On(n);let i=n,r=ie;if(t in e.normal)return e.property[e.normal[t]];if(t.length>4&&t.slice(0,4)==="data"&&c0.test(n)){if(n.charAt(4)==="-"){const a=n.slice(5).replace(It,p0);i="data"+a.charAt(0).toUpperCase()+a.slice(1)}else{const a=n.slice(4);if(!It.test(a)){let o=a.replace(u0,d0);o.charAt(0)!=="-"&&(o="-"+o),n="data"+o}}r=Zn}return new r(i,n)}function d0(e){return"-"+e.toLowerCase()}function p0(e){return e.charAt(1).toUpperCase()}const f0=Ci([Fi,a0,Ti,Ii,Bi],"html"),et=Ci([Fi,s0,Ti,Ii,Bi],"svg");function m0(e){return e.join(" ").trim()}var Bt=/\/\*(?:[^*]|\*(?!\/))*\*\//g,g0=/\n/g,y0=/^\s*/,w0=/^(\*?[-#/*\\\w]+(\[[0-9a-z_-]+\])?)\s*/,b0=/^:\s*/,k0=/^((?:'(?:\\.|[^'\\])*'|"(?:\\.|[^"\\])*"|url\((?:'(?:\\.|[^'\\])*'|"(?:\\.|[^"\\])*"|[^)]*)\)|[^};])+)/,v0=/^[;\s]*/,D0=`
`,qt="/",Rt="*",Ne="",x0="comment",_0="declaration";function A0(e,n){if(typeof e!="string")throw new TypeError("First argument must be a string");if(!e)return[];n=n||{};var t=1,i=1;function r(f){var w=f.match(g0);w&&(t+=w.length);var D=f.lastIndexOf(D0);i=~D?f.length-D:i+f.length}function a(){var f={line:t,column:i};return function(w){return w.position=new o(f),u(),w}}function o(f){this.start=f,this.end={line:t,column:i},this.source=n.source}o.prototype.content=e;function s(f){var w=new Error(n.source+":"+t+":"+i+": "+f);if(w.reason=f,w.filename=n.source,w.line=t,w.column=i,w.source=e,!n.silent)throw w}function l(f){var w=f.exec(e);if(w){var D=w[0];return r(D),e=e.slice(D.length),w}}function u(){l(y0)}function c(f){for(var w;w=h();)f.push(w);return f}function h(){var f=a();if(!(qt!=e.charAt(0)||Rt!=e.charAt(1))){for(var w=2;Ne!=e.charAt(w)&&(Rt!=e.charAt(w)||qt!=e.charAt(w+1));)++w;if(w+=2,Ne===e.charAt(w-1))return s("End of comment missing");var D=e.slice(2,w-2);return i+=2,r(D),e=e.slice(w),i+=2,f({type:x0,comment:D})}}function p(){var f=a(),w=l(w0);if(w){if(h(),!l(b0))return s("property missing ':'");var D=l(k0),y=f({type:_0,property:w[0].replace(Bt,Ne).trim(),value:D?D[0].replace(Bt,Ne).trim():Ne});return l(v0),y}}function d(){var f=[];c(f);for(var w;w=p();)f.push(w),c(f);return f}return u(),d()}function C0(e,n){let t=null;if(!e||typeof e!="string")return t;const i=A0(e),r=typeof n=="function";return i.forEach(a=>{if(a.type!=="declaration")return;const{property:o,value:s}=a;r?n(o,s,a):s&&(t=t??{},t[o]=s)}),t}const qi=Ri("end"),nt=Ri("start");function Ri(e){return n;function n(t){const i=t&&t.position&&t.position[e]||{};if(typeof i.line=="number"&&i.line>0&&typeof i.column=="number"&&i.column>0)return{line:i.line,column:i.column,offset:typeof i.offset=="number"&&i.offset>-1?i.offset:void 0}}}function F0(e){const n=nt(e),t=qi(e);if(n&&t)return{start:n,end:t}}function Ue(e){return!e||typeof e!="object"?"":"position"in e||"type"in e?Pt(e.position):"start"in e||"end"in e?Pt(e):"line"in e||"column"in e?Hn(e):""}function Hn(e){return zt(e&&e.line)+":"+zt(e&&e.column)}function Pt(e){return Hn(e&&e.start)+"-"+Hn(e&&e.end)}function zt(e){return e&&typeof e=="number"?e:1}class Z extends Error{constructor(n,t,i){super(),typeof t=="string"&&(i=t,t=void 0);let r="",a={},o=!1;if(t&&("line"in t&&"column"in t?a={place:t}:"start"in t&&"end"in t?a={place:t}:"type"in t?a={ancestors:[t],place:t.position}:a={...t}),typeof n=="string"?r=n:!a.cause&&n&&(o=!0,r=n.message,a.cause=n),!a.ruleId&&!a.source&&typeof i=="string"){const l=i.indexOf(":");l===-1?a.ruleId=i:(a.source=i.slice(0,l),a.ruleId=i.slice(l+1))}if(!a.place&&a.ancestors&&a.ancestors){const l=a.ancestors[a.ancestors.length-1];l&&(a.place=l.position)}const s=a.place&&"start"in a.place?a.place.start:a.place;this.ancestors=a.ancestors||void 0,this.cause=a.cause||void 0,this.column=s?s.column:void 0,this.fatal=void 0,this.file="",this.message=r,this.line=s?s.line:void 0,this.name=Ue(a.place)||"1:1",this.place=a.place||void 0,this.reason=this.message,this.ruleId=a.ruleId||void 0,this.source=a.source||void 0,this.stack=o&&a.cause&&typeof a.cause.stack=="string"?a.cause.stack:"",this.actual=void 0,this.expected=void 0,this.note=void 0,this.url=void 0}}Z.prototype.file="";Z.prototype.name="";Z.prototype.reason="";Z.prototype.message="";Z.prototype.stack="";Z.prototype.column=void 0;Z.prototype.line=void 0;Z.prototype.ancestors=void 0;Z.prototype.cause=void 0;Z.prototype.fatal=void 0;Z.prototype.place=void 0;Z.prototype.ruleId=void 0;Z.prototype.source=void 0;const tt={}.hasOwnProperty,E0=new Map,S0=/[A-Z]/g,T0=/-([a-z])/g,I0=new Set(["table","tbody","thead","tfoot","tr"]),B0=new Set(["td","th"]),Pi="https://github.com/syntax-tree/hast-util-to-jsx-runtime";function q0(e,n){if(!n||n.Fragment===void 0)throw new TypeError("Expected `Fragment` in options");const t=n.filePath||void 0;let i;if(n.development){if(typeof n.jsxDEV!="function")throw new TypeError("Expected `jsxDEV` in options when `development: true`");i=H0(t,n.jsxDEV)}else{if(typeof n.jsx!="function")throw new TypeError("Expected `jsx` in production options");if(typeof n.jsxs!="function")throw new TypeError("Expected `jsxs` in production options");i=N0(t,n.jsx,n.jsxs)}const r={Fragment:n.Fragment,ancestors:[],components:n.components||{},create:i,elementAttributeNameCase:n.elementAttributeNameCase||"react",evaluater:n.createEvaluater?n.createEvaluater():void 0,filePath:t,ignoreInvalidStyle:n.ignoreInvalidStyle||!1,passKeys:n.passKeys!==!1,passNode:n.passNode||!1,schema:n.space==="svg"?et:f0,stylePropertyNameCase:n.stylePropertyNameCase||"dom",tableCellAlignToStyle:n.tableCellAlignToStyle!==!1},a=zi(r,e,void 0);return a&&typeof a!="string"?a:r.create(e,r.Fragment,{children:a||void 0},void 0)}function zi(e,n,t){if(n.type==="element")return R0(e,n,t);if(n.type==="mdxFlowExpression"||n.type==="mdxTextExpression")return P0(e,n);if(n.type==="mdxJsxFlowElement"||n.type==="mdxJsxTextElement")return L0(e,n,t);if(n.type==="mdxjsEsm")return z0(e,n);if(n.type==="root")return O0(e,n,t);if(n.type==="text")return M0(e,n)}function R0(e,n,t){const i=e.schema;let r=i;n.tagName.toLowerCase()==="svg"&&i.space==="html"&&(r=et,e.schema=r),e.ancestors.push(n);const a=Oi(e,n.tagName,!1),o=j0(e,n);let s=rt(e,n);return I0.has(n.tagName)&&(s=s.filter(function(l){return typeof l=="string"?!r0(l):!0})),Li(e,o,a,n),it(o,s),e.ancestors.pop(),e.schema=i,e.create(n,a,o,t)}function P0(e,n){if(n.data&&n.data.estree&&e.evaluater){const i=n.data.estree.body[0];return i.type,e.evaluater.evaluateExpression(i.expression)}$e(e,n.position)}function z0(e,n){if(n.data&&n.data.estree&&e.evaluater)return e.evaluater.evaluateProgram(n.data.estree);$e(e,n.position)}function L0(e,n,t){const i=e.schema;let r=i;n.name==="svg"&&i.space==="html"&&(r=et,e.schema=r),e.ancestors.push(n);const a=n.name===null?e.Fragment:Oi(e,n.name,!0),o=U0(e,n),s=rt(e,n);return Li(e,o,a,n),it(o,s),e.ancestors.pop(),e.schema=i,e.create(n,a,o,t)}function O0(e,n,t){const i={};return it(i,rt(e,n)),e.create(n,e.Fragment,i,t)}function M0(e,n){return n.value}function Li(e,n,t,i){typeof t!="string"&&t!==e.Fragment&&e.passNode&&(n.node=i)}function it(e,n){if(n.length>0){const t=n.length>1?n:n[0];t&&(e.children=t)}}function N0(e,n,t){return i;function i(r,a,o,s){const u=Array.isArray(o.children)?t:n;return s?u(a,o,s):u(a,o)}}function H0(e,n){return t;function t(i,r,a,o){const s=Array.isArray(a.children),l=nt(i);return n(r,a,o,s,{columnNumber:l?l.column-1:void 0,fileName:e,lineNumber:l?l.line:void 0},void 0)}}function j0(e,n){const t={};let i,r;for(r in n.properties)if(r!=="children"&&tt.call(n.properties,r)){const a=V0(e,r,n.properties[r]);if(a){const[o,s]=a;e.tableCellAlignToStyle&&o==="align"&&typeof s=="string"&&B0.has(n.tagName)?i=s:t[o]=s}}if(i){const a=t.style||(t.style={});a[e.stylePropertyNameCase==="css"?"text-align":"textAlign"]=i}return t}function U0(e,n){const t={};for(const i of n.attributes)if(i.type==="mdxJsxExpressionAttribute")if(i.data&&i.data.estree&&e.evaluater){const a=i.data.estree.body[0];a.type;const o=a.expression;o.type;const s=o.properties[0];s.type,Object.assign(t,e.evaluater.evaluateExpression(s.argument))}else $e(e,n.position);else{const{name:r}=i;let a;if(i.value&&typeof i.value=="object")if(i.value.data&&i.value.data.estree&&e.evaluater){const s=i.value.data.estree.body[0];s.type,a=e.evaluater.evaluateExpression(s.expression)}else $e(e,n.position);else a=i.value===null?!0:i.value;t[r]=a}return t}function rt(e,n){const t=[];let i=-1;const r=e.passKeys?new Map:E0;for(;++i<n.children.length;){const a=n.children[i];let o;if(e.passKeys){const l=a.type==="element"?a.tagName:a.type==="mdxJsxFlowElement"||a.type==="mdxJsxTextElement"?a.name:void 0;if(l){const u=r.get(l)||0;o=l+"-"+u,r.set(l,u+1)}}const s=zi(e,a,o);s!==void 0&&t.push(s)}return t}function V0(e,n,t){if(t==null||typeof t=="number"&&Number.isNaN(t))return;const i=h0(e.schema,n);return Array.isArray(t)&&(t=i.commaSeparated?Zr(t):m0(t)),i.property==="style"?["style",typeof t=="object"?e.stylePropertyNameCase==="dom"?t:$0(t):W0(e,String(t))]:[e.elementAttributeNameCase==="react"&&i.space?l0[i.property]||i.property:i.attribute,t]}function W0(e,n){const t={};try{C0(n,function(i,r){if(i&&r){let a=i;a.slice(0,2)!=="--"&&(a=a.toLowerCase(),e.stylePropertyNameCase==="dom"&&(a.slice(0,4)==="-ms-"&&(a=a.slice(1)),a=a.replace(T0,Y0))),t[a]=r}})}catch(i){if(e.ignoreInvalidStyle)return{};const r=i,a=new Z("Cannot parse `style` attribute",{ancestors:e.ancestors,cause:r,ruleId:"style",source:"hast-util-to-jsx-runtime"});throw a.file=e.filePath||void 0,a.url=Pi+"#cannot-parse-style-attribute",a}return t}function Oi(e,n,t){let i;if(!t)i={type:"Literal",value:n};else if(n.includes(".")){const r=n.split(".");let a=-1,o;for(;++a<r.length;){const s=Et(r[a])?{type:"Identifier",name:r[a]}:{type:"Literal",value:r[a]};o=o?{type:"MemberExpression",object:o,property:s,computed:!!(a&&s.type==="Literal"),optional:!1}:s}i=o}else i=Et(n)&&!/^[a-z]/.test(n)?{type:"Identifier",name:n}:{type:"Literal",value:n};if(i.type==="Literal"){const r=i.value;return tt.call(e.components,r)?e.components[r]:r}if(e.evaluater)return e.evaluater.evaluateExpression(i);$e(e)}function $e(e,n){const t=new Z("Cannot handle MDX estrees without `createEvaluater`",{ancestors:e.ancestors,place:n,ruleId:"mdx-estree",source:"hast-util-to-jsx-runtime"});throw t.file=e.filePath||void 0,t.url=Pi+"#cannot-handle-mdx-estrees-without-createevaluater",t}function $0(e){const n={};let t;for(t in e)tt.call(e,t)&&(n[K0(t)]=e[t]);return n}function K0(e){if(e.slice(0,2)==="--")return e;let n=e.replace(S0,G0);return n.slice(0,3)==="ms-"&&(n="-"+n),n}function G0(e){return"-"+e.toLowerCase()}function Y0(e,n){return n.toUpperCase()}const xn={action:["form"],cite:["blockquote","del","ins","q"],data:["object"],formAction:["button","input"],href:["a","area","base","link"],icon:["menuitem"],itemId:null,manifest:["html"],ping:["a","area"],poster:["video"],src:["audio","embed","iframe","img","input","script","source","track","video"]},Q0={};function ot(e,n){const t=Q0,i=typeof t.includeImageAlt=="boolean"?t.includeImageAlt:!0,r=typeof t.includeHtml=="boolean"?t.includeHtml:!0;return Mi(e,i,r)}function Mi(e,n,t){if(X0(e)){if("value"in e)return e.type==="html"&&!t?"":e.value;if(n&&"alt"in e&&e.alt)return e.alt;if("children"in e)return Lt(e.children,n,t)}return Array.isArray(e)?Lt(e,n,t):""}function Lt(e,n,t){const i=[];let r=-1;for(;++r<e.length;)i[r]=Mi(e[r],n,t);return i.join("")}function X0(e){return!!(e&&typeof e=="object")}const Ot=document.createElement("i");function at(e){const n="&"+e+";";Ot.innerHTML=n;const t=Ot.textContent;return t.charCodeAt(t.length-1)===59&&e!=="semi"||t===n?!1:t}function ce(e,n,t,i){const r=e.length;let a=0,o;if(n<0?n=-n>r?0:r+n:n=n>r?r:n,t=t>0?t:0,i.length<1e4)o=Array.from(i),o.unshift(n,t),e.splice(...o);else for(t&&e.splice(n,t);a<i.length;)o=i.slice(a,a+1e4),o.unshift(n,0),e.splice(...o),a+=1e4,n+=1e4}function ae(e,n){return e.length>0?(ce(e,e.length,0,n),e):n}const Mt={}.hasOwnProperty;function Ni(e){const n={};let t=-1;for(;++t<e.length;)J0(n,e[t]);return n}function J0(e,n){let t;for(t in n){const r=(Mt.call(e,t)?e[t]:void 0)||(e[t]={}),a=n[t];let o;if(a)for(o in a){Mt.call(r,o)||(r[o]=[]);const s=a[o];Z0(r[o],Array.isArray(s)?s:s?[s]:[])}}}function Z0(e,n){let t=-1;const i=[];for(;++t<n.length;)(n[t].add==="after"?e:i).push(n[t]);ce(e,0,0,i)}function Hi(e,n){const t=Number.parseInt(e,n);return t<9||t===11||t>13&&t<32||t>126&&t<160||t>55295&&t<57344||t>64975&&t<65008||(t&65535)===65535||(t&65535)===65534||t>1114111?"�":String.fromCodePoint(t)}function he(e){return e.replace(/[\t\n\r ]+/g," ").replace(/^ | $/g,"").toLowerCase().toUpperCase()}const Q=De(/[A-Za-z]/),X=De(/[\dA-Za-z]/),eo=De(/[#-'*+\--9=?A-Z^-~]/);function sn(e){return e!==null&&(e<32||e===127)}const jn=De(/\d/),no=De(/[\dA-Fa-f]/),ji=De(/[!-/:-@[-`{-~]/);function T(e){return e!==null&&e<-2}function U(e){return e!==null&&(e<0||e===32)}function z(e){return e===-2||e===-1||e===32}const dn=De(new RegExp("\\p{P}|\\p{S}","u")),Ce=De(/\s/);function De(e){return n;function n(t){return t!==null&&t>-1&&e.test(String.fromCharCode(t))}}function Pe(e){const n=[];let t=-1,i=0,r=0;for(;++t<e.length;){const a=e.charCodeAt(t);let o="";if(a===37&&X(e.charCodeAt(t+1))&&X(e.charCodeAt(t+2)))r=2;else if(a<128)/[!#$&-;=?-Z_a-z~]/.test(String.fromCharCode(a))||(o=String.fromCharCode(a));else if(a>55295&&a<57344){const s=e.charCodeAt(t+1);a<56320&&s>56319&&s<57344?(o=String.fromCharCode(a,s),r=1):o="�"}else o=String.fromCharCode(a);o&&(n.push(e.slice(i,t),encodeURIComponent(o)),i=t+r+1,o=""),r&&(t+=r,r=0)}return n.join("")+e.slice(i)}function M(e,n,t,i){const r=i?i-1:1/0;let a=0;return o;function o(l){return z(l)?(e.enter(t),s(l)):n(l)}function s(l){return z(l)&&a++<r?(e.consume(l),s):(e.exit(t),n(l))}}function Ui(e,n,t,i,r,a){let o=0;return s;function s(c){return z(c)?(e.enter(i),l(c)):u(c)}function l(c){return z(c)&&o<a?(e.consume(c),o++,l):(e.exit(i),u(c))}function u(c){return o>=r?n(c):t(c)}}const to={tokenize:io};function io(e){const n=e.attempt(this.parser.constructs.contentInitial,i,r);let t;return n;function i(s){if(s===null){e.consume(s);return}return e.enter("lineEnding"),e.consume(s),e.exit("lineEnding"),M(e,n,"linePrefix")}function r(s){return e.enter("paragraph"),a(s)}function a(s){const l=e.enter("chunkText",{contentType:"text",previous:t});return t&&(t.next=l),t=l,o(s)}function o(s){if(s===null){e.exit("chunkText"),e.exit("paragraph"),e.consume(s);return}return T(s)?(e.consume(s),e.exit("chunkText"),a):(e.consume(s),o)}}let ln=class{constructor(){this.index=new Map,this.map=[]}add(n,t,i){Nt(this,n,t,i,!1)}addBefore(n,t,i){Nt(this,n,t,i,!0)}consume(n){if(this.map.sort(function(a,o){return a[0]-o[0]}),this.map.length===0)return;let t=this.map.length;const i=[];for(;t>0;)t-=1,i.push(n.slice(this.map[t][0]+this.map[t][1]),this.map[t][2]),n.length=this.map[t][0];i.push(n.slice()),n.length=0;let r=i.pop();for(;r;){for(const a of r)n.push(a);r=i.pop()}this.map.length=0,this.index.clear()}};function Nt(e,n,t,i,r){if(t===0&&i.length===0)return;const a=e.index.get(n);if(a){a[1]+=t,r?(i.push(...a[2]),a[2]=i):a[2].push(...i);return}const o=[n,t,i];e.map.push(o),e.index.set(n,o)}const ro={tokenize:oo},Ht={tokenize:ao};function oo(e){const n=this,t=[];let i=0,r,a,o;return s;function s(x){if(i<t.length){const E=t[i];return n.containerState=E[1],e.attempt(E[0].continuation,l,u)(x)}return u(x)}function l(x){if(i++,n.containerState._closeFlow){n.containerState._closeFlow=void 0,r&&_();const E=n.events.length;let S=E,v;for(;S--;)if(n.events[S][0]==="exit"&&n.events[S][1].type==="chunkFlow"){v=n.events[S][1].end;break}y(i);let B=E;for(;B<n.events.length;)n.events[B][1].end={...v},B++;const N=new ln;return N.add(S+1,0,n.events.slice(E)),N.add(E,B-E,[]),N.consume(n.events),u(x)}return s(x)}function u(x){if(i===t.length){if(!r)return p(x);if(r.currentConstruct&&r.currentConstruct.concrete)return f(x);n.interrupt=!!(r.currentConstruct&&!r._gfmTableDynamicInterruptHack)}return n.containerState={},e.check(Ht,c,h)(x)}function c(x){return r&&_(),y(i),p(x)}function h(x){return n.parser.lazy[n.now().line]=i!==t.length,o=n.now().offset,f(x)}function p(x){return n.containerState={},e.attempt(Ht,d,f)(x)}function d(x){return i++,t.push([n.currentConstruct,n.containerState]),p(x)}function f(x){if(x===null){r&&_(),y(0),e.consume(x);return}return r=r||n.parser.flow(n.now()),e.enter("chunkFlow",{_tokenizer:r,contentType:"flow",previous:a}),w(x)}function w(x){if(x===null){D(e.exit("chunkFlow"),!0),y(0),e.consume(x);return}return T(x)?(e.consume(x),D(e.exit("chunkFlow")),i=0,n.interrupt=void 0,s):(e.consume(x),w)}function D(x,E){const S=n.sliceStream(x);if(E&&S.push(null),x.previous=a,a&&(a.next=x),a=x,r.defineSkip(x.start),r.write(S),n.parser.lazy[x.start.line]){let v=r.events.length;for(;v--;)if(r.events[v][1].start.offset<o&&(!r.events[v][1].end||r.events[v][1].end.offset>o))return;const B=n.events.length;let N=B,$,b;for(;N--;)if(n.events[N][0]==="exit"&&n.events[N][1].type==="chunkFlow"){if($){b=n.events[N][1].end;break}$=!0}for(y(i),v=B;v<n.events.length;)n.events[v][1].end={...b},v++;const F=new ln;F.add(N+1,0,n.events.slice(B)),F.add(B,v-B,[]),F.consume(n.events)}}function y(x){let E=t.length;for(;E-- >x;){const S=t[E];n.containerState=S[1],S[0].exit.call(n,e)}t.length=x}function _(){r.write([null]),a=void 0,r=void 0,n.containerState._closeFlow=void 0}}function ao(e,n,t){return M(e,e.attempt(this.parser.constructs.document,n,t),"linePrefix",this.parser.constructs.disable.null.includes("codeIndented")?void 0:4)}function ve(e){if(e===null||U(e)||Ce(e))return 1;if(dn(e))return 2}function pn(e,n,t){const i=[];let r=-1;for(;++r<e.length;){const a=e[r].resolveAll;a&&!i.includes(a)&&(n=a(n,t),i.push(a))}return n}const Un={name:"attention",resolveAll:so,tokenize:lo};function so(e,n){let t=-1,i;for(;++t<e.length;)if(e[t][0]==="enter"&&e[t][1].type==="attentionSequence"&&e[t][1]._close){let r=t;for(;r--;)if(e[r][0]==="exit"&&e[r][1].type==="attentionSequence"&&e[r][1]._open&&n.sliceSerialize(e[r][1]).charCodeAt(0)===n.sliceSerialize(e[t][1]).charCodeAt(0)){if((e[r][1]._close||e[t][1]._open)&&(e[t][1].end.offset-e[t][1].start.offset)%3&&!((e[r][1].end.offset-e[r][1].start.offset+e[t][1].end.offset-e[t][1].start.offset)%3))continue;const a=e[r][1].end.offset-e[r][1].start.offset>1&&e[t][1].end.offset-e[t][1].start.offset>1?2:1,o={...e[r][1].end},s={...e[t][1].start};jt(o,-a),jt(s,a);const l={type:a>1?"strongSequence":"emphasisSequence",start:o,end:{...e[r][1].end}},u={type:a>1?"strongSequence":"emphasisSequence",start:{...e[t][1].start},end:s},c={type:a>1?"strongText":"emphasisText",start:{...e[r][1].end},end:{...e[t][1].start}},h={type:a>1?"strong":"emphasis",start:{...l.start},end:{...u.end}};e[r][1].end={...l.start},e[t][1].start={...u.end},i=[],e[r][1].end.offset-e[r][1].start.offset&&(i=ae(i,[["enter",e[r][1],n],["exit",e[r][1],n]])),i=ae(i,[["enter",h,n],["enter",l,n],["exit",l,n],["enter",c,n]]),i=ae(i,pn(n.parser.constructs.insideSpan.null,e.slice(r+1,t),n)),i=ae(i,[["exit",c,n],["enter",u,n],["exit",u,n],["exit",h,n]]);let p=0;e[t][1].end.offset-e[t][1].start.offset&&(p=2,i=ae(i,[["enter",e[t][1],n],["exit",e[t][1],n]])),ce(e,r-1,t-r+3,i),t=r+i.length-p-2;break}}for(t=-1;++t<e.length;)e[t][1].type==="attentionSequence"&&(e[t][1].type="data");return e}function lo(e,n){const t=this.parser.constructs.attentionMarkers.null,i=this.previous,r=ve(i);let a;return o;function o(l){return a=l,e.enter("attentionSequence"),s(l)}function s(l){if(l===a)return e.consume(l),s;const u=e.exit("attentionSequence"),c=ve(l),h=!c||c===2&&r||t.includes(l)&&l!==42&&l!==95,p=!r||r===2&&c||t.includes(i)&&i!==42&&i!==95;return u._open=!!(a===42?h:h&&(r||!p)),u._close=!!(a===42?p:p&&(c||!h)),n(l)}}function jt(e,n){e.column+=n,e.offset+=n,e._bufferIndex+=n}const uo={name:"autolink",tokenize:co};function co(e,n,t){let i=0;return r;function r(d){return e.enter("autolink"),e.enter("autolinkMarker"),e.consume(d),e.exit("autolinkMarker"),e.enter("autolinkProtocol"),a}function a(d){return Q(d)?(e.consume(d),o):d===64?t(d):u(d)}function o(d){return d===43||d===45||d===46||X(d)?(i=1,s(d)):u(d)}function s(d){return d===58?(e.consume(d),i=0,l):(d===43||d===45||d===46||X(d))&&i++<32?(e.consume(d),s):(i=0,u(d))}function l(d){return d===62?(e.exit("autolinkProtocol"),e.enter("autolinkMarker"),e.consume(d),e.exit("autolinkMarker"),e.exit("autolink"),n):d===null||d===32||d===60||sn(d)?t(d):(e.consume(d),l)}function u(d){return d===64?(e.consume(d),c):eo(d)?(e.consume(d),u):t(d)}function c(d){return X(d)?h(d):t(d)}function h(d){return d===46?(e.consume(d),i=0,c):d===62?(e.exit("autolinkProtocol").type="autolinkEmail",e.enter("autolinkMarker"),e.consume(d),e.exit("autolinkMarker"),e.exit("autolink"),n):p(d)}function p(d){if((d===45||X(d))&&i++<63){const f=d===45?p:h;return e.consume(d),f}return t(d)}}const Ge={partial:!0,tokenize:ho};function ho(e,n,t){return i;function i(a){return z(a)?M(e,r,"linePrefix")(a):r(a)}function r(a){return a===null||T(a)?n(a):t(a)}}const Vi={continuation:{tokenize:fo},exit:mo,name:"blockQuote",tokenize:po};function po(e,n,t){const i=this;return r;function r(o){if(o===62){const s=i.containerState;return s.open||(e.enter("blockQuote",{_container:!0}),s.open=!0),e.enter("blockQuotePrefix"),e.enter("blockQuoteMarker"),e.consume(o),e.exit("blockQuoteMarker"),a}return t(o)}function a(o){return z(o)?(e.enter("blockQuotePrefixWhitespace"),e.consume(o),e.exit("blockQuotePrefixWhitespace"),e.exit("blockQuotePrefix"),n):(e.exit("blockQuotePrefix"),n(o))}}function fo(e,n,t){const i=this;return r;function r(o){return z(o)?M(e,a,"linePrefix",i.parser.constructs.disable.null.includes("codeIndented")?void 0:4)(o):a(o)}function a(o){return e.attempt(Vi,n,t)(o)}}function mo(e){e.exit("blockQuote")}const Wi={name:"characterEscape",tokenize:go};function go(e,n,t){return i;function i(a){return e.enter("characterEscape"),e.enter("escapeMarker"),e.consume(a),e.exit("escapeMarker"),r}function r(a){return ji(a)?(e.enter("characterEscapeValue"),e.consume(a),e.exit("characterEscapeValue"),e.exit("characterEscape"),n):t(a)}}const $i={name:"characterReference",tokenize:yo};function yo(e,n,t){const i=this;let r=0,a,o;return s;function s(h){return e.enter("characterReference"),e.enter("characterReferenceMarker"),e.consume(h),e.exit("characterReferenceMarker"),l}function l(h){return h===35?(e.enter("characterReferenceMarkerNumeric"),e.consume(h),e.exit("characterReferenceMarkerNumeric"),u):(e.enter("characterReferenceValue"),a=31,o=X,c(h))}function u(h){return h===88||h===120?(e.enter("characterReferenceMarkerHexadecimal"),e.consume(h),e.exit("characterReferenceMarkerHexadecimal"),e.enter("characterReferenceValue"),a=6,o=no,c):(e.enter("characterReferenceValue"),a=7,o=jn,c(h))}function c(h){if(h===59&&r){const p=e.exit("characterReferenceValue");return o===X&&!at(i.sliceSerialize(p))?t(h):(e.enter("characterReferenceMarker"),e.consume(h),e.exit("characterReferenceMarker"),e.exit("characterReference"),n)}return o(h)&&r++<a?(e.consume(h),c):t(h)}}const Vn={partial:!0,tokenize:wo};function wo(e,n,t){const i=this;return r;function r(o){return o===null?t(o):(e.enter("lineEnding"),e.consume(o),e.exit("lineEnding"),a)}function a(o){return i.parser.lazy[i.now().line]?t(o):n(o)}}const Ut={concrete:!0,name:"codeFenced",tokenize:bo};function bo(e,n,t){const i=this,r={partial:!0,tokenize:S};let a=0,o=0,s;return l;function l(v){return u(v)}function u(v){const B=i.events[i.events.length-1];return a=B&&B[1].type==="linePrefix"?B[2].sliceSerialize(B[1],!0).length:0,s=v,e.enter("codeFenced"),e.enter("codeFencedFence"),e.enter("codeFencedFenceSequence"),c(v)}function c(v){return v===s?(o++,e.consume(v),c):o<3?t(v):(e.exit("codeFencedFenceSequence"),z(v)?M(e,h,"whitespace")(v):h(v))}function h(v){return v===null||T(v)?(e.exit("codeFencedFence"),i.interrupt?n(v):e.check(Vn,w,E)(v)):(e.enter("codeFencedFenceInfo"),e.enter("chunkString",{contentType:"string"}),p(v))}function p(v){return v===null||T(v)?(e.exit("chunkString"),e.exit("codeFencedFenceInfo"),h(v)):z(v)?(e.exit("chunkString"),e.exit("codeFencedFenceInfo"),M(e,d,"whitespace")(v)):v===96&&v===s?t(v):(e.consume(v),p)}function d(v){return v===null||T(v)?h(v):(e.enter("codeFencedFenceMeta"),e.enter("chunkString",{contentType:"string"}),f(v))}function f(v){return v===null||T(v)?(e.exit("chunkString"),e.exit("codeFencedFenceMeta"),h(v)):v===96&&v===s?t(v):(e.consume(v),f)}function w(v){return e.attempt(r,E,D)(v)}function D(v){return e.enter("lineEnding"),e.consume(v),e.exit("lineEnding"),y}function y(v){return a>0&&z(v)?M(e,_,"linePrefix",a+1)(v):_(v)}function _(v){return v===null||T(v)?e.check(Vn,w,E)(v):(e.enter("codeFlowValue"),x(v))}function x(v){return v===null||T(v)?(e.exit("codeFlowValue"),_(v)):(e.consume(v),x)}function E(v){return e.exit("codeFenced"),n(v)}function S(v,B,N){let $=0;return b;function b(O){return v.enter("lineEnding"),v.consume(O),v.exit("lineEnding"),F}function F(O){return v.enter("codeFencedFence"),z(O)?M(v,I,"linePrefix",i.parser.constructs.disable.null.includes("codeIndented")?void 0:4)(O):I(O)}function I(O){return O===s?(v.enter("codeFencedFenceSequence"),H(O)):N(O)}function H(O){return O===s?($++,v.consume(O),H):$>=o?(v.exit("codeFencedFenceSequence"),z(O)?M(v,W,"whitespace")(O):W(O)):N(O)}function W(O){return O===null||T(O)?(v.exit("codeFencedFence"),B(O)):N(O)}}}const _n={name:"codeIndented",tokenize:vo},ko={partial:!0,tokenize:Do};function vo(e,n,t){return i;function i(s){return e.enter("codeIndented"),Ui(e,r,t,"linePrefix",4,4)(s)}function r(s){return s===null?o(s):T(s)?e.attempt(ko,r,o)(s):(e.enter("codeFlowValue"),a(s))}function a(s){return s===null||T(s)?(e.exit("codeFlowValue"),r(s)):(e.consume(s),a)}function o(s){return e.exit("codeIndented"),n(s)}}function Do(e,n,t){const i=this;return r;function r(o){return i.parser.lazy[i.now().line]?t(o):T(o)?(e.enter("lineEnding"),e.consume(o),e.exit("lineEnding"),r):Ui(e,n,a,"linePrefix",4,4)(o)}function a(o){return T(o)?r(o):t(o)}}const xo={name:"codeText",previous:Ao,resolve:_o,tokenize:Co};function _o(e){let n=e.length-4,t=3,i,r;if((e[t][1].type==="lineEnding"||e[t][1].type==="space")&&(e[n][1].type==="lineEnding"||e[n][1].type==="space")){for(i=t;++i<n;)if(e[i][1].type==="codeTextData"){e[t][1].type="codeTextPadding",e[n][1].type="codeTextPadding",t+=2,n-=2;break}}for(i=t-1,n++;++i<=n;)r===void 0?i!==n&&e[i][1].type!=="lineEnding"&&(r=i):(i===n||e[i][1].type==="lineEnding")&&(e[r][1].type="codeTextData",i!==r+2&&(e[r][1].end=e[i-1][1].end,e.splice(r+2,i-r-2),n-=i-r-2,i=r+2),r=void 0);return e}function Ao(e){return e!==96||this.events[this.events.length-1][1].type==="characterEscape"}function Co(e,n,t){let i=0,r,a;return o;function o(h){return e.enter("codeText"),e.enter("codeTextSequence"),s(h)}function s(h){return h===96?(e.consume(h),i++,s):(e.exit("codeTextSequence"),l(h))}function l(h){return h===null?t(h):h===32?(e.enter("space"),e.consume(h),e.exit("space"),l):h===96?(a=e.enter("codeTextSequence"),r=0,c(h)):T(h)?(e.enter("lineEnding"),e.consume(h),e.exit("lineEnding"),l):(e.enter("codeTextData"),u(h))}function u(h){return h===null||h===32||h===96||T(h)?(e.exit("codeTextData"),l(h)):(e.consume(h),u)}function c(h){return h===96?(e.consume(h),r++,c):r===i?(e.exit("codeTextSequence"),e.exit("codeText"),n(h)):(a.type="codeTextData",u(h))}}class Fo{constructor(n){this.left=n?[...n]:[],this.right=[]}get(n){if(n<0||n>=this.left.length+this.right.length)throw new RangeError("Cannot access index `"+n+"` in a splice buffer of size `"+(this.left.length+this.right.length)+"`");return n<this.left.length?this.left[n]:this.right[this.right.length-n+this.left.length-1]}get length(){return this.left.length+this.right.length}shift(){return this.setCursor(0),this.right.pop()}slice(n,t){const i=t??Number.POSITIVE_INFINITY;return i<this.left.length?this.left.slice(n,i):n>this.left.length?this.right.slice(this.right.length-i+this.left.length,this.right.length-n+this.left.length).reverse():this.left.slice(n).concat(this.right.slice(this.right.length-i+this.left.length).reverse())}splice(n,t,i){const r=t||0;this.setCursor(Math.trunc(n));const a=this.right.splice(this.right.length-r,Number.POSITIVE_INFINITY);return i&&He(this.left,i),a.reverse()}pop(){return this.setCursor(Number.POSITIVE_INFINITY),this.left.pop()}push(n){this.setCursor(Number.POSITIVE_INFINITY),this.left.push(n)}pushMany(n){this.setCursor(Number.POSITIVE_INFINITY),He(this.left,n)}unshift(n){this.setCursor(0),this.right.push(n)}unshiftMany(n){this.setCursor(0),He(this.right,n.reverse())}setCursor(n){if(!(n===this.left.length||n>this.left.length&&this.right.length===0||n<0&&this.left.length===0))if(n<this.left.length){const t=this.left.splice(n,Number.POSITIVE_INFINITY);He(this.right,t.reverse())}else{const t=this.right.splice(this.left.length+this.right.length-n,Number.POSITIVE_INFINITY);He(this.left,t.reverse())}}}function He(e,n){let t=0;if(n.length<1e4)e.push(...n);else for(;t<n.length;)e.push(...n.slice(t,t+1e4)),t+=1e4}function Ki(e){const n={};let t=-1,i,r,a,o,s,l,u;const c=new Fo(e);for(;++t<c.length;){for(;t in n;)t=n[t];if(i=c.get(t),t&&i[1].type==="chunkFlow"&&c.get(t-1)[1].type==="listItemPrefix"&&(l=i[1]._tokenizer.events,a=0,a<l.length&&l[a][1].type==="lineEndingBlank"&&(a+=2),a<l.length&&l[a][1].type==="content"))for(;++a<l.length&&l[a][1].type!=="content";)l[a][1].type==="chunkText"&&(l[a][1]._isInFirstContentOfListItem=!0,a++);if(i[0]==="enter")i[1].contentType&&(Object.assign(n,Eo(c,t)),t=n[t],u=!0);else if(i[1]._container){for(a=t,r=void 0;a--;)if(o=c.get(a),o[1].type==="lineEnding"||o[1].type==="lineEndingBlank")o[0]==="enter"&&(r&&(c.get(r)[1].type="lineEndingBlank"),o[1].type="lineEnding",r=a);else if(!(o[1].type==="linePrefix"||o[1].type==="listItemIndent"))break;r&&(i[1].end={...c.get(r)[1].start},s=c.slice(r,t),s.unshift(i),c.splice(r,t-r+1,s))}}return ce(e,0,Number.POSITIVE_INFINITY,c.slice(0)),!u}function Eo(e,n){const t=e.get(n)[1],i=e.get(n)[2];let r=n-1;const a=[];let o=t._tokenizer;o||(o=i.parser[t.contentType](t.start),t._contentTypeTextTrailing&&(o._contentTypeTextTrailing=!0));const s=o.events,l=[],u={};let c,h,p=-1,d=t,f=0,w=0;const D=[w];for(;d;){for(;e.get(++r)[1]!==d;);a.push(r),d._tokenizer||(c=i.sliceStream(d),d.next||c.push(null),h&&o.defineSkip(d.start),d._isInFirstContentOfListItem&&(o._gfmTasklistFirstContentOfListItem=!0),o.write(c),d._isInFirstContentOfListItem&&(o._gfmTasklistFirstContentOfListItem=void 0)),h=d,d=d.next}for(d=t;++p<s.length;)s[p][0]==="exit"&&s[p-1][0]==="enter"&&s[p][1].type===s[p-1][1].type&&s[p][1].start.line!==s[p][1].end.line&&(w=p+1,D.push(w),d._tokenizer=void 0,d.previous=void 0,d=d.next);for(o.events=[],d?(d._tokenizer=void 0,d.previous=void 0):D.pop(),p=D.length;p--;){const y=s.slice(D[p],D[p+1]),_=a.pop();l.push([_,_+y.length-1]),e.splice(_,2,y)}for(l.reverse(),p=-1;++p<l.length;)u[f+l[p][0]]=f+l[p][1],f+=l[p][1]-l[p][0]-1;return u}const So={resolve:Io,tokenize:Bo},To={partial:!0,tokenize:qo};function Io(e){return Ki(e),e}function Bo(e,n){let t;return i;function i(s){return e.enter("content"),t=e.enter("chunkContent",{contentType:"content"}),r(s)}function r(s){return s===null?a(s):T(s)?e.check(To,o,a)(s):(e.consume(s),r)}function a(s){return e.exit("chunkContent"),e.exit("content"),n(s)}function o(s){return e.consume(s),e.exit("chunkContent"),t.next=e.enter("chunkContent",{contentType:"content",previous:t}),t=t.next,r}}function qo(e,n,t){const i=this;return r;function r(o){return e.exit("chunkContent"),e.enter("lineEnding"),e.consume(o),e.exit("lineEnding"),M(e,a,"linePrefix")}function a(o){if(o===null||T(o))return t(o);const s=i.events[i.events.length-1];return!i.parser.constructs.disable.null.includes("codeIndented")&&s&&s[1].type==="linePrefix"&&s[2].sliceSerialize(s[1],!0).length>=4?n(o):e.interrupt(i.parser.constructs.flow,t,n)(o)}}function Gi(e,n,t,i,r,a,o,s,l){const u=l||Number.POSITIVE_INFINITY;let c=0;return h;function h(y){return y===60?(e.enter(i),e.enter(r),e.enter(a),e.consume(y),e.exit(a),p):y===null||y===32||y===41||sn(y)?t(y):(e.enter(i),e.enter(o),e.enter(s),e.enter("chunkString",{contentType:"string"}),w(y))}function p(y){return y===62?(e.enter(a),e.consume(y),e.exit(a),e.exit(r),e.exit(i),n):(e.enter(s),e.enter("chunkString",{contentType:"string"}),d(y))}function d(y){return y===62?(e.exit("chunkString"),e.exit(s),p(y)):y===null||y===60||T(y)?t(y):(e.consume(y),y===92?f:d)}function f(y){return y===60||y===62||y===92?(e.consume(y),d):d(y)}function w(y){return!c&&(y===null||y===41||U(y))?(e.exit("chunkString"),e.exit(s),e.exit(o),e.exit(i),n(y)):c<u&&y===40?(e.consume(y),c++,w):y===41?(e.consume(y),c--,w):y===null||y===32||y===40||sn(y)?t(y):(e.consume(y),y===92?D:w)}function D(y){return y===40||y===41||y===92?(e.consume(y),w):w(y)}}function Yi(e,n,t,i,r,a){const o=this;let s=0,l;return u;function u(d){return e.enter(i),e.enter(r),e.consume(d),e.exit(r),e.enter(a),c}function c(d){return s>999||d===null||d===91||d===93&&!l||d===94&&!s&&"_hiddenFootnoteSupport"in o.parser.constructs?t(d):d===93?(e.exit(a),e.enter(r),e.consume(d),e.exit(r),e.exit(i),n):T(d)?(e.enter("lineEnding"),e.consume(d),e.exit("lineEnding"),c):(e.enter("chunkString",{contentType:"string"}),h(d))}function h(d){return d===null||d===91||d===93||T(d)||s++>999?(e.exit("chunkString"),c(d)):(e.consume(d),l||(l=!z(d)),d===92?p:h)}function p(d){return d===91||d===92||d===93?(e.consume(d),s++,h):h(d)}}function Qi(e,n,t,i,r,a){let o;return s;function s(p){return p===34||p===39||p===40?(e.enter(i),e.enter(r),e.consume(p),e.exit(r),o=p===40?41:p,l):t(p)}function l(p){return p===o?(e.enter(r),e.consume(p),e.exit(r),e.exit(i),n):(e.enter(a),u(p))}function u(p){return p===o?(e.exit(a),l(o)):p===null?t(p):T(p)?(e.enter("lineEnding"),e.consume(p),e.exit("lineEnding"),M(e,u,"linePrefix")):(e.enter("chunkString",{contentType:"string"}),c(p))}function c(p){return p===o||p===null||T(p)?(e.exit("chunkString"),u(p)):(e.consume(p),p===92?h:c)}function h(p){return p===o||p===92?(e.consume(p),c):c(p)}}function Ve(e,n){let t;return i;function i(r){return T(r)?(e.enter("lineEnding"),e.consume(r),e.exit("lineEnding"),t=!0,i):z(r)?M(e,i,t?"linePrefix":"lineSuffix")(r):n(r)}}const Ro={name:"definition",tokenize:zo},Po={partial:!0,tokenize:Lo};function zo(e,n,t){const i=this;let r;return a;function a(d){return e.enter("definition"),o(d)}function o(d){return Yi.call(i,e,s,t,"definitionLabel","definitionLabelMarker","definitionLabelString")(d)}function s(d){return r=he(i.sliceSerialize(i.events[i.events.length-1][1]).slice(1,-1)),d===58?(e.enter("definitionMarker"),e.consume(d),e.exit("definitionMarker"),l):t(d)}function l(d){return U(d)?Ve(e,u)(d):u(d)}function u(d){return Gi(e,c,t,"definitionDestination","definitionDestinationLiteral","definitionDestinationLiteralMarker","definitionDestinationRaw","definitionDestinationString")(d)}function c(d){return e.attempt(Po,h,h)(d)}function h(d){return z(d)?M(e,p,"whitespace")(d):p(d)}function p(d){return d===null||T(d)?(e.exit("definition"),i.parser.defined.push(r),n(d)):t(d)}}function Lo(e,n,t){return i;function i(s){return U(s)?Ve(e,r)(s):t(s)}function r(s){return Qi(e,a,t,"definitionTitle","definitionTitleMarker","definitionTitleString")(s)}function a(s){return z(s)?M(e,o,"whitespace")(s):o(s)}function o(s){return s===null||T(s)?n(s):t(s)}}const Oo={name:"hardBreakEscape",tokenize:Mo};function Mo(e,n,t){return i;function i(a){return e.enter("hardBreakEscape"),e.consume(a),r}function r(a){return T(a)?(e.exit("hardBreakEscape"),n(a)):t(a)}}const No={name:"headingAtx",resolve:Ho,tokenize:jo};function Ho(e,n){let t=e.length-2,i=3;if(e[i][1].type==="whitespace"&&(i+=2),t-2>i&&e[t][1].type==="whitespace"&&(t-=2),e[t][1].type==="atxHeadingSequence"&&(i===t-1||t-4>i&&e[t-2][1].type==="whitespace")&&(t-=i+1===t?2:4),t>i){const r={type:"atxHeadingText",start:e[i][1].start,end:e[t][1].end},a={type:"chunkText",start:e[i][1].start,end:e[t][1].end,contentType:"text"};ce(e,i,t-i+1,[["enter",r,n],["enter",a,n],["exit",a,n],["exit",r,n]])}return e}function jo(e,n,t){let i=0;return r;function r(c){return e.enter("atxHeading"),a(c)}function a(c){return e.enter("atxHeadingSequence"),o(c)}function o(c){return c===35&&i++<6?(e.consume(c),o):c===null||U(c)?(e.exit("atxHeadingSequence"),s(c)):t(c)}function s(c){return c===35?(e.enter("atxHeadingSequence"),l(c)):c===null||T(c)?(e.exit("atxHeading"),n(c)):z(c)?M(e,s,"whitespace")(c):(e.enter("atxHeadingText"),u(c))}function l(c){return c===35?(e.consume(c),l):(e.exit("atxHeadingSequence"),s(c))}function u(c){return c===null||c===35||U(c)?(e.exit("atxHeadingText"),s(c)):(e.consume(c),u)}}const Xi=["address","article","aside","base","basefont","blockquote","body","caption","center","col","colgroup","dd","details","dialog","dir","div","dl","dt","fieldset","figcaption","figure","footer","form","frame","frameset","h1","h2","h3","h4","h5","h6","head","header","hr","html","iframe","legend","li","link","main","menu","menuitem","nav","noframes","ol","optgroup","option","p","param","search","section","summary","table","tbody","td","tfoot","th","thead","title","tr","track","ul"],Wn=["pre","script","style","textarea"],Uo={concrete:!0,name:"htmlFlow",resolveTo:Wo,tokenize:$o},Vo={partial:!0,tokenize:Ko};function Wo(e){let n=e.length;for(;n--&&!(e[n][0]==="enter"&&e[n][1].type==="htmlFlow"););return n>1&&e[n-2][1].type==="linePrefix"&&(e[n][1].start=e[n-2][1].start,e[n+1][1].start=e[n-2][1].start,e.splice(n-2,2)),e}function $o(e,n,t){const i=this;let r,a,o,s,l;return u;function u(g){return c(g)}function c(g){return e.enter("htmlFlow"),e.enter("htmlFlowData"),e.consume(g),h}function h(g){return g===33?(e.consume(g),p):g===47?(e.consume(g),a=!0,w):g===63?(e.consume(g),r=3,i.interrupt?n:m):Q(g)?(e.consume(g),o=String.fromCharCode(g),D):t(g)}function p(g){return g===45?(e.consume(g),r=2,d):g===91?(e.consume(g),r=5,s=0,f):Q(g)?(e.consume(g),r=4,i.interrupt?n:m):t(g)}function d(g){return g===45?(e.consume(g),i.interrupt?n:m):t(g)}function f(g){const ue="CDATA[";return g===ue.charCodeAt(s++)?(e.consume(g),s===ue.length?i.interrupt?n:I:f):t(g)}function w(g){return Q(g)?(e.consume(g),o=String.fromCharCode(g),D):t(g)}function D(g){if(g===null||g===47||g===62||U(g)){const ue=g===47,Ee=o.toLowerCase();return!ue&&!a&&Wn.includes(Ee)?(r=1,i.interrupt?n(g):I(g)):Xi.includes(o.toLowerCase())?(r=6,ue?(e.consume(g),y):i.interrupt?n(g):I(g)):(r=7,i.interrupt&&!i.parser.lazy[i.now().line]?t(g):a?_(g):x(g))}return g===45||X(g)?(e.consume(g),o+=String.fromCharCode(g),D):t(g)}function y(g){return g===62?(e.consume(g),i.interrupt?n:I):t(g)}function _(g){return z(g)?(e.consume(g),_):b(g)}function x(g){return g===47?(e.consume(g),b):g===58||g===95||Q(g)?(e.consume(g),E):z(g)?(e.consume(g),x):b(g)}function E(g){return g===45||g===46||g===58||g===95||X(g)?(e.consume(g),E):S(g)}function S(g){return g===61?(e.consume(g),v):z(g)?(e.consume(g),S):x(g)}function v(g){return g===null||g===60||g===61||g===62||g===96?t(g):g===34||g===39?(e.consume(g),l=g,B):z(g)?(e.consume(g),v):N(g)}function B(g){return g===l?(e.consume(g),l=null,$):g===null||T(g)?t(g):(e.consume(g),B)}function N(g){return g===null||g===34||g===39||g===47||g===60||g===61||g===62||g===96||U(g)?S(g):(e.consume(g),N)}function $(g){return g===47||g===62||z(g)?x(g):t(g)}function b(g){return g===62?(e.consume(g),F):t(g)}function F(g){return g===null||T(g)?I(g):z(g)?(e.consume(g),F):t(g)}function I(g){return g===45&&r===2?(e.consume(g),J):g===60&&r===1?(e.consume(g),Y):g===62&&r===4?(e.consume(g),le):g===63&&r===3?(e.consume(g),m):g===93&&r===5?(e.consume(g),me):T(g)&&(r===6||r===7)?(e.exit("htmlFlowData"),e.check(Vo,ge,H)(g)):g===null||T(g)?(e.exit("htmlFlowData"),H(g)):(e.consume(g),I)}function H(g){return e.check(Vn,W,ge)(g)}function W(g){return e.enter("lineEnding"),e.consume(g),e.exit("lineEnding"),O}function O(g){return g===null||T(g)?H(g):(e.enter("htmlFlowData"),I(g))}function J(g){return g===45?(e.consume(g),m):I(g)}function Y(g){return g===47?(e.consume(g),o="",se):I(g)}function se(g){if(g===62){const ue=o.toLowerCase();return Wn.includes(ue)?(e.consume(g),le):I(g)}return Q(g)&&o.length<8?(e.consume(g),o+=String.fromCharCode(g),se):I(g)}function me(g){return g===93?(e.consume(g),m):I(g)}function m(g){return g===62?(e.consume(g),le):g===45&&r===2?(e.consume(g),m):I(g)}function le(g){return g===null||T(g)?(e.exit("htmlFlowData"),ge(g)):(e.consume(g),le)}function ge(g){return e.exit("htmlFlow"),n(g)}}function Ko(e,n,t){return i;function i(r){return e.enter("lineEnding"),e.consume(r),e.exit("lineEnding"),e.attempt(Ge,n,t)}}const Go={name:"htmlText",tokenize:Yo};function Yo(e,n,t){const i=this;let r,a,o;return s;function s(m){return e.enter("htmlText"),e.enter("htmlTextData"),e.consume(m),l}function l(m){return m===33?(e.consume(m),u):m===47?(e.consume(m),S):m===63?(e.consume(m),x):Q(m)?(e.consume(m),N):t(m)}function u(m){return m===45?(e.consume(m),c):m===91?(e.consume(m),a=0,f):Q(m)?(e.consume(m),_):t(m)}function c(m){return m===45?(e.consume(m),d):t(m)}function h(m){return m===null?t(m):m===45?(e.consume(m),p):T(m)?(o=h,Y(m)):(e.consume(m),h)}function p(m){return m===45?(e.consume(m),d):h(m)}function d(m){return m===62?J(m):m===45?p(m):h(m)}function f(m){const le="CDATA[";return m===le.charCodeAt(a++)?(e.consume(m),a===le.length?w:f):t(m)}function w(m){return m===null?t(m):m===93?(e.consume(m),D):T(m)?(o=w,Y(m)):(e.consume(m),w)}function D(m){return m===93?(e.consume(m),y):w(m)}function y(m){return m===62?J(m):m===93?(e.consume(m),y):w(m)}function _(m){return m===null||m===62?J(m):T(m)?(o=_,Y(m)):(e.consume(m),_)}function x(m){return m===null?t(m):m===63?(e.consume(m),E):T(m)?(o=x,Y(m)):(e.consume(m),x)}function E(m){return m===62?J(m):x(m)}function S(m){return Q(m)?(e.consume(m),v):t(m)}function v(m){return m===45||X(m)?(e.consume(m),v):B(m)}function B(m){return T(m)?(o=B,Y(m)):z(m)?(e.consume(m),B):J(m)}function N(m){return m===45||X(m)?(e.consume(m),N):m===47||m===62||U(m)?$(m):t(m)}function $(m){return m===47?(e.consume(m),J):m===58||m===95||Q(m)?(e.consume(m),b):T(m)?(o=$,Y(m)):z(m)?(e.consume(m),$):J(m)}function b(m){return m===45||m===46||m===58||m===95||X(m)?(e.consume(m),b):F(m)}function F(m){return m===61?(e.consume(m),I):T(m)?(o=F,Y(m)):z(m)?(e.consume(m),F):$(m)}function I(m){return m===null||m===60||m===61||m===62||m===96?t(m):m===34||m===39?(e.consume(m),r=m,H):T(m)?(o=I,Y(m)):z(m)?(e.consume(m),I):(e.consume(m),W)}function H(m){return m===r?(e.consume(m),r=void 0,O):m===null?t(m):T(m)?(o=H,Y(m)):(e.consume(m),H)}function W(m){return m===null||m===34||m===39||m===60||m===61||m===96?t(m):m===47||m===62||U(m)?$(m):(e.consume(m),W)}function O(m){return m===47||m===62||U(m)?$(m):t(m)}function J(m){return m===62?(e.consume(m),e.exit("htmlTextData"),e.exit("htmlText"),n):t(m)}function Y(m){return e.exit("htmlTextData"),e.enter("lineEnding"),e.consume(m),e.exit("lineEnding"),se}function se(m){return z(m)?M(e,me,"linePrefix",i.parser.constructs.disable.null.includes("codeIndented")?void 0:4)(m):me(m)}function me(m){return e.enter("htmlTextData"),o(m)}}const st={name:"labelEnd",resolveAll:Zo,resolveTo:ea,tokenize:na},Qo={tokenize:ta},Xo={tokenize:ia},Jo={tokenize:ra};function Zo(e){let n=-1;const t=[];for(;++n<e.length;){const i=e[n][1];if(t.push(e[n]),i.type==="labelImage"||i.type==="labelLink"||i.type==="labelEnd"){const r=i.type==="labelImage"?4:2;i.type="data",n+=r}}return e.length!==t.length&&ce(e,0,e.length,t),e}function ea(e,n){let t=e.length,i=0,r,a,o;for(;t--;){const c=e[t][1];if(r){if(c.type==="link"||c.type==="labelLink"&&c._inactive)break;e[t][0]==="enter"&&c.type==="labelLink"&&(c._inactive=!0)}else if(a){if(e[t][0]==="enter"&&(c.type==="labelImage"||c.type==="labelLink")&&!c._balanced&&(r=t,c.type!=="labelLink")){i=2;break}}else c.type==="labelEnd"&&(a=t)}const s={type:e[r][1].type==="labelLink"?"link":"image",start:{...e[r][1].start},end:{...e[e.length-1][1].end}},l={type:"label",start:{...e[r][1].start},end:{...e[a][1].end}},u={type:"labelText",start:{...e[r+i+2][1].end},end:{...e[a-2][1].start}};return o=[["enter",s,n],["enter",l,n]],o=ae(o,e.slice(r+1,r+i+3)),o=ae(o,[["enter",u,n]]),o=ae(o,pn(n.parser.constructs.insideSpan.null,e.slice(r+i+4,a-3),n)),o=ae(o,[["exit",u,n],e[a-2],e[a-1],["exit",l,n]]),o=ae(o,e.slice(a+1)),o=ae(o,[["exit",s,n]]),ce(e,r,e.length,o),e}function na(e,n,t){const i=this,r=i._labelStarts;let a,o;if(r){for(;r.length>0&&r[r.length-1]._balanced;)r.pop();a=r[r.length-1]}return s;function s(p){return a?a._inactive?h(p):(o=i.parser.defined.includes(he(i.sliceSerialize({start:a.end,end:i.now()}))),e.enter("labelEnd"),e.enter("labelMarker"),e.consume(p),e.exit("labelMarker"),e.exit("labelEnd"),l):t(p)}function l(p){return p===40?e.attempt(Qo,c,o?c:h)(p):p===91?e.attempt(Xo,c,o?u:h)(p):o?c(p):h(p)}function u(p){return e.attempt(Jo,c,h)(p)}function c(p){return r.pop(),n(p)}function h(p){return a._balanced=!0,t(p)}}function ta(e,n,t){return i;function i(h){return e.enter("resource"),e.enter("resourceMarker"),e.consume(h),e.exit("resourceMarker"),r}function r(h){return U(h)?Ve(e,a)(h):a(h)}function a(h){return h===41?c(h):Gi(e,o,s,"resourceDestination","resourceDestinationLiteral","resourceDestinationLiteralMarker","resourceDestinationRaw","resourceDestinationString",32)(h)}function o(h){return U(h)?Ve(e,l)(h):c(h)}function s(h){return t(h)}function l(h){return h===34||h===39||h===40?Qi(e,u,t,"resourceTitle","resourceTitleMarker","resourceTitleString")(h):c(h)}function u(h){return U(h)?Ve(e,c)(h):c(h)}function c(h){return h===41?(e.enter("resourceMarker"),e.consume(h),e.exit("resourceMarker"),e.exit("resource"),n):t(h)}}function ia(e,n,t){const i=this;return r;function r(s){return Yi.call(i,e,a,o,"reference","referenceMarker","referenceString")(s)}function a(s){return i.parser.defined.includes(he(i.sliceSerialize(i.events[i.events.length-1][1]).slice(1,-1)))?n(s):t(s)}function o(s){return t(s)}}function ra(e,n,t){return i;function i(a){return e.enter("reference"),e.enter("referenceMarker"),e.consume(a),e.exit("referenceMarker"),r}function r(a){return a===93?(e.enter("referenceMarker"),e.consume(a),e.exit("referenceMarker"),e.exit("reference"),n):t(a)}}const oa={name:"labelStartImage",resolveAll:st.resolveAll,tokenize:aa};function aa(e,n,t){const i=this;let r;return a;function a(l){return e.enter("labelImage"),e.enter("labelImageMarker"),e.consume(l),e.exit("labelImageMarker"),o}function o(l){return l===91?(e.enter("labelMarker"),e.consume(l),e.exit("labelMarker"),r=e.exit("labelImage"),s):t(l)}function s(l){return l===94&&"_hiddenFootnoteSupport"in i.parser.constructs?t(l):(i._labelStarts=i._labelStarts||[],i._labelStarts.push(r),n(l))}}const sa={name:"labelStartLink",resolveAll:st.resolveAll,tokenize:la};function la(e,n,t){const i=this;let r;return a;function a(s){return e.enter("labelLink"),e.enter("labelMarker"),e.consume(s),e.exit("labelMarker"),r=e.exit("labelLink"),o}function o(s){return s===94&&"_hiddenFootnoteSupport"in i.parser.constructs?t(s):(i._labelStarts=i._labelStarts||[],i._labelStarts.push(r),n(s))}}const An={name:"lineEnding",tokenize:ua};function ua(e,n){return t;function t(i){return e.enter("lineEnding"),e.consume(i),e.exit("lineEnding"),M(e,n,"linePrefix")}}const rn={name:"thematicBreak",tokenize:ca};function ca(e,n,t){let i=0,r;return a;function a(u){return e.enter("thematicBreak"),o(u)}function o(u){return r=u,s(u)}function s(u){return u===r?(e.enter("thematicBreakSequence"),l(u)):i>=3&&(u===null||T(u))?(e.exit("thematicBreak"),n(u)):t(u)}function l(u){return u===r?(e.consume(u),i++,l):(e.exit("thematicBreakSequence"),z(u)?M(e,s,"whitespace")(u):s(u))}}const te={continuation:{tokenize:fa},exit:ga,name:"list",tokenize:pa},ha={partial:!0,tokenize:ya},da={partial:!0,tokenize:ma};function pa(e,n,t){const i=this,r=i.events[i.events.length-1];let a=r&&r[1].type==="linePrefix"?r[2].sliceSerialize(r[1],!0).length:0,o=0;return s;function s(d){const f=i.containerState.type||(d===42||d===43||d===45?"listUnordered":"listOrdered");if(f==="listUnordered"?!i.containerState.marker||d===i.containerState.marker:jn(d)){if(i.containerState.type||(i.containerState.type=f,e.enter(f,{_container:!0})),f==="listUnordered")return e.enter("listItemPrefix"),d===42||d===45?e.check(rn,t,u)(d):u(d);if(!i.interrupt||d===49)return e.enter("listItemPrefix"),e.enter("listItemValue"),l(d)}return t(d)}function l(d){return jn(d)&&++o<10?(e.consume(d),l):(!i.interrupt||o<2)&&(i.containerState.marker?d===i.containerState.marker:d===41||d===46)?(e.exit("listItemValue"),u(d)):t(d)}function u(d){return e.enter("listItemMarker"),e.consume(d),e.exit("listItemMarker"),i.containerState.marker=i.containerState.marker||d,e.check(Ge,i.interrupt?t:c,e.attempt(ha,p,h))}function c(d){return i.containerState.initialBlankLine=!0,a++,p(d)}function h(d){return z(d)?(e.enter("listItemPrefixWhitespace"),e.consume(d),e.exit("listItemPrefixWhitespace"),p):t(d)}function p(d){return i.containerState.size=a+i.sliceSerialize(e.exit("listItemPrefix"),!0).length,n(d)}}function fa(e,n,t){const i=this;return i.containerState._closeFlow=void 0,e.check(Ge,r,a);function r(s){return i.containerState.furtherBlankLines=i.containerState.furtherBlankLines||i.containerState.initialBlankLine,M(e,n,"listItemIndent",i.containerState.size+1)(s)}function a(s){return i.containerState.furtherBlankLines||!z(s)?(i.containerState.furtherBlankLines=void 0,i.containerState.initialBlankLine=void 0,o(s)):(i.containerState.furtherBlankLines=void 0,i.containerState.initialBlankLine=void 0,e.attempt(da,n,o)(s))}function o(s){return i.containerState._closeFlow=!0,i.interrupt=void 0,M(e,e.attempt(te,n,t),"linePrefix",i.parser.constructs.disable.null.includes("codeIndented")?void 0:4)(s)}}function ma(e,n,t){const i=this;return M(e,r,"listItemIndent",i.containerState.size+1);function r(a){const o=i.events[i.events.length-1];return o&&o[1].type==="listItemIndent"&&o[2].sliceSerialize(o[1],!0).length===i.containerState.size?n(a):t(a)}}function ga(e){e.exit(this.containerState.type)}function ya(e,n,t){const i=this;return M(e,r,"listItemPrefixWhitespace",i.parser.constructs.disable.null.includes("codeIndented")?void 0:5);function r(a){const o=i.events[i.events.length-1];return!z(a)&&o&&o[1].type==="listItemPrefixWhitespace"?n(a):t(a)}}const Vt={name:"setextUnderline",resolveTo:wa,tokenize:ba};function wa(e,n){const t=new ln;let i=e.length,r,a,o;for(;i--;)if(e[i][0]==="enter"){if(e[i][1].type==="content"){r=i;break}e[i][1].type==="paragraph"&&(a=i)}else e[i][1].type==="content"&&t.add(i,1,[]),!o&&e[i][1].type==="definition"&&(o=i);const s={type:"setextHeading",start:{...e[r][1].start},end:{...e[e.length-1][1].end}};return e[a][1].type="setextHeadingText",o?(t.add(a,0,[["enter",s,n]]),t.add(o+1,0,[["exit",e[r][1],n]]),e[r][1].end={...e[o][1].end}):e[r][1]=s,t.add(e.length,0,[["exit",s,n]]),t.consume(e),e}function ba(e,n,t){const i=this;let r;return a;function a(u){let c=i.events.length,h;for(;c--;)if(i.events[c][1].type!=="lineEnding"&&i.events[c][1].type!=="linePrefix"&&i.events[c][1].type!=="content"){h=i.events[c][1].type==="paragraph";break}return!i.parser.lazy[i.now().line]&&(i.interrupt||h)?(e.enter("setextHeadingLine"),r=u,o(u)):t(u)}function o(u){return e.enter("setextHeadingLineSequence"),s(u)}function s(u){return u===r?(e.consume(u),s):(e.exit("setextHeadingLineSequence"),z(u)?M(e,l,"lineSuffix")(u):l(u))}function l(u){return u===null||T(u)?(e.exit("setextHeadingLine"),n(u)):t(u)}}const ka={tokenize:va};function va(e){const n=this,t=e.attempt(Ge,i,e.attempt(this.parser.constructs.flowInitial,r,M(e,e.attempt(this.parser.constructs.flow,r,e.attempt(So,r)),"linePrefix")));return t;function i(a){if(a===null){e.consume(a);return}return e.enter("lineEndingBlank"),e.consume(a),e.exit("lineEndingBlank"),n.currentConstruct=void 0,t}function r(a){if(a===null){e.consume(a);return}return e.enter("lineEnding"),e.consume(a),e.exit("lineEnding"),n.currentConstruct=void 0,t}}const Da={resolveAll:Zi()},xa=Ji("string"),_a=Ji("text");function Ji(e){return{resolveAll:Zi(e==="text"?Aa:void 0),tokenize:n};function n(t){const i=this,r=this.parser.constructs[e],a=t.attempt(r,o,s);return o;function o(c){return u(c)?a(c):s(c)}function s(c){if(c===null){t.consume(c);return}return t.enter("data"),t.consume(c),l}function l(c){return u(c)?(t.exit("data"),a(c)):(t.consume(c),l)}function u(c){if(c===null)return!0;const h=r[c];let p=-1;if(h)for(;++p<h.length;){const d=h[p];if(!d.previous||d.previous.call(i,i.previous))return!0}return!1}}}function Zi(e){return n;function n(t,i){let r=-1,a;for(;++r<=t.length;)a===void 0?t[r]&&t[r][1].type==="data"&&(a=r,r++):(!t[r]||t[r][1].type!=="data")&&(r!==a+2&&(t[a][1].end=t[r-1][1].end,t.splice(a+2,r-a-2),r=a+2),a=void 0);return e?e(t,i):t}}function Aa(e,n){const t=new ln;let i=0;for(;++i<=e.length;)if((i===e.length||e[i][1].type==="lineEnding")&&e[i-1][1].type==="data"){const r=e[i-1][1],a=n.sliceStream(r);let o=a.length,s=-1,l=0,u;for(;o--;){const c=a[o];if(typeof c=="string"){for(s=c.length;c.charCodeAt(s-1)===32;)l++,s--;if(s)break;s=-1}else if(c===-2)u=!0,l++;else if(c!==-1){o++;break}}if(n._contentTypeTextTrailing&&i===e.length&&(l=0),l){const c={type:i===e.length||u||l<2?"lineSuffix":"hardBreakTrailing",start:{_bufferIndex:o?s:r.start._bufferIndex+s,_index:r.start._index+o,line:r.end.line,column:r.end.column-l,offset:r.end.offset-l},end:{...r.end}};r.end={...c.start},r.start.offset===r.end.offset?Object.assign(r,c):t.add(i,0,[["enter",c,n],["exit",c,n]])}i++}return t.consume(e),e}const Ca={42:te,43:te,45:te,48:te,49:te,50:te,51:te,52:te,53:te,54:te,55:te,56:te,57:te,62:Vi},Fa={91:Ro},Ea={[-2]:_n,[-1]:_n,32:_n},Sa={35:No,42:rn,45:[Vt,rn],60:Uo,61:Vt,95:rn,96:Ut,126:Ut},Ta={38:$i,92:Wi},Ia={[-5]:An,[-4]:An,[-3]:An,33:oa,38:$i,42:Un,60:[uo,Go],91:sa,92:[Oo,Wi],93:st,95:Un,96:xo},Ba={null:[Un,Da]},qa={null:[42,95]},Ra={null:[]},Pa=Object.freeze(Object.defineProperty({__proto__:null,attentionMarkers:qa,contentInitial:Fa,disable:Ra,document:Ca,flow:Sa,flowInitial:Ea,insideSpan:Ba,string:Ta,text:Ia},Symbol.toStringTag,{value:"Module"}));function za(e,n,t){let i={_bufferIndex:-1,_index:0,line:t&&t.line||1,column:t&&t.column||1,offset:t&&t.offset||0};const r={},a=[];let o=[],s=[];const l={attempt:B(S),check:B(v),consume:_,enter:x,exit:E,interrupt:B(v,{interrupt:!0})},u={code:null,containerState:{},defineSkip:w,events:[],now:f,parser:e,previous:null,sliceSerialize:p,sliceStream:d,write:h};let c=n.tokenize.call(u,l);return n.resolveAll&&a.push(n),u;function h(F){return o=ae(o,F),D(),o[o.length-1]!==null?[]:(N(n,0),u.events=pn(a,u.events,u),u.events)}function p(F,I){return Oa(d(F),I)}function d(F){return La(o,F)}function f(){const{_bufferIndex:F,_index:I,line:H,column:W,offset:O}=i;return{_bufferIndex:F,_index:I,line:H,column:W,offset:O}}function w(F){r[F.line]=F.column,b()}function D(){for(;i._index<o.length;){const F=o[i._index];if(typeof F=="string"){const I=i._index;for(i._bufferIndex<0&&(i._bufferIndex=0);i._index===I&&i._bufferIndex<F.length;)y(F.charCodeAt(i._bufferIndex))}else y(F)}}function y(F){c=c(F)}function _(F){T(F)?(i.line++,i.column=1,i.offset+=F===-3?2:1,b()):F!==-1&&(i.column++,i.offset++),i._bufferIndex<0?i._index++:(i._bufferIndex++,i._bufferIndex===o[i._index].length&&(i._bufferIndex=-1,i._index++)),u.previous=F}function x(F,I){const H=I||{};return H.type=F,H.start=f(),u.events.push(["enter",H,u]),s.push(H),H}function E(F){const I=s.pop();return I.end=f(),u.events.push(["exit",I,u]),I}function S(F,I){N(F,I.from)}function v(F,I){I.restore()}function B(F,I){return H;function H(W,O,J){let Y,se,me,m;return Array.isArray(W)?ge(W):"tokenize"in W?ge([W]):le(W);function le(G){return ze;function ze(be){const Se=be!==null&&G[be],Te=be!==null&&G.null,bn=[...Array.isArray(Se)?Se:Se?[Se]:[],...Array.isArray(Te)?Te:Te?[Te]:[]];return ge(bn)(be)}}function ge(G){return Y=G,se=0,G.length===0?J:g(G[se])}function g(G){return ze;function ze(be){return m=$(),me=G,G.partial||(u.currentConstruct=G),G.name&&u.parser.constructs.disable.null.includes(G.name)?Ee():G.tokenize.call(I?Object.assign(Object.create(u),I):u,l,ue,Ee)(be)}}function ue(G){return F(me,m),O}function Ee(G){return m.restore(),++se<Y.length?g(Y[se]):J}}}function N(F,I){F.resolveAll&&!a.includes(F)&&a.push(F),F.resolve&&ce(u.events,I,u.events.length-I,F.resolve(u.events.slice(I),u)),F.resolveTo&&(u.events=F.resolveTo(u.events,u))}function $(){const F=f(),I=u.previous,H=u.currentConstruct,W=u.events.length,O=Array.from(s);return{from:W,restore:J};function J(){i=F,u.previous=I,u.currentConstruct=H,u.events.length=W,s=O,b()}}function b(){i.line in r&&i.column<2&&(i.column=r[i.line],i.offset+=r[i.line]-1)}}function La(e,n){const t=n.start._index,i=n.start._bufferIndex,r=n.end._index,a=n.end._bufferIndex;let o;if(t===r)o=[e[t].slice(i,a)];else{if(o=e.slice(t,r),i>-1){const s=o[0];typeof s=="string"?o[0]=s.slice(i):o.shift()}a>0&&o.push(e[r].slice(0,a))}return o}function Oa(e,n){let t=-1;const i=[];let r;for(;++t<e.length;){const a=e[t];let o;if(typeof a=="string")o=a;else switch(a){case-5:{o="\r";break}case-4:{o=`
`;break}case-3:{o=`\r
`;break}case-2:{o=n?" ":"	";break}case-1:{if(!n&&r)continue;o=" ";break}default:o=String.fromCharCode(a)}r=a===-2,i.push(o)}return i.join("")}function Ma(e){const i={constructs:Ni([Pa,...(e||{}).extensions||[]]),content:r(to),defined:[],document:r(ro),flow:r(ka),lazy:{},string:r(xa),text:r(_a)};return i;function r(a){return o;function o(s){return za(i,a,s)}}}function Na(e){for(;!Ki(e););return e}const Wt=/[\0\t\n\r]/g;function Ha(){let e=1,n="",t=!0,i;return r;function r(a,o,s){a=n+(typeof a=="string"?a.toString():new TextDecoder(o||void 0).decode(a));const l=[];let u=0;for(n="",t&&(a.charCodeAt(0)===65279&&u++,t=void 0);u<a.length;){Wt.lastIndex=u;const c=Wt.exec(a),h=c&&c.index!==void 0?c.index:a.length,p=a.charCodeAt(h);if(!c){n=a.slice(u);break}if(p===10&&u===h&&i)l.push(-3),i=void 0;else switch(i&&(l.push(-5),i=void 0),u<h&&(l.push(a.slice(u,h)),e+=h-u),p){case 0:{l.push(65533),e++;break}case 9:{const d=Math.ceil(e/4)*4;for(l.push(-2);e++<d;)l.push(-1);break}case 10:{l.push(-4),e=1;break}default:i=!0,e=1}u=h+1}return s&&(i&&l.push(-5),n&&l.push(n),l.push(null)),l}}const ja=/\\([!-/:-@[-`{-~])|&(#(?:\d{1,7}|x[\da-f]{1,6})|[\da-z]{1,31});/gi;function Ua(e){return e.replace(ja,Va)}function Va(e,n,t){if(n)return n;if(t.charCodeAt(0)===35){const r=t.charCodeAt(1),a=r===120||r===88;return Hi(t.slice(a?2:1),a?16:10)}return at(t)||e}const er={}.hasOwnProperty;function Wa(e,n,t){return n&&typeof n=="object"&&(t=n,n=void 0),$a(t)(Na(Ma(t).document().write(Ha()(e,n,!0))))}function $a(e){const n={afterExit:[],beforeEnter:[],transforms:[],canContainEols:["emphasis","fragment","heading","paragraph","strong"],enter:{autolink:o(At),autolinkProtocol:b,autolinkEmail:b,atxHeading:o(Dt),blockQuote:o(bn),characterEscape:b,characterReference:b,codeFenced:o(vt),codeFencedFenceInfo:s,codeFencedFenceMeta:s,codeIndented:o(vt,s),codeText:o(Lr,s),codeTextData:b,data:b,codeFlowValue:b,definition:o(Or),definitionDestinationString:s,definitionLabelString:s,definitionTitleString:s,emphasis:o(Mr),hardBreakEscape:o(xt),hardBreakTrailing:o(xt),htmlFlow:o(_t,s),htmlFlowData:b,htmlText:o(_t,s),htmlTextData:b,image:o(Nr),label:s,link:o(At),listItem:o(Hr),listItemValue:d,listOrdered:o(Ct,p),listUnordered:o(Ct),paragraph:o(jr),reference:ue,referenceString:s,resourceDestinationString:s,resourceTitleString:s,setextHeading:o(Dt),strong:o(Ur),thematicBreak:o(Wr)},exit:{atxHeading:u(),atxHeadingSequence:v,autolink:u(),autolinkEmail:Te,autolinkProtocol:Se,blockQuote:u(),characterEscapeValue:F,characterReferenceMarkerHexadecimal:G,characterReferenceMarkerNumeric:G,characterReferenceValue:ze,characterReference:be,codeFenced:u(y),codeFencedFence:D,codeFencedFenceInfo:f,codeFencedFenceMeta:w,codeFlowValue:F,codeIndented:u(_),codeText:u(J),codeTextData:F,data:F,definition:u(),definitionDestinationString:S,definitionLabelString:x,definitionTitleString:E,emphasis:u(),hardBreakEscape:u(H),hardBreakTrailing:u(H),htmlFlow:u(W),htmlFlowData:F,htmlText:u(O),htmlTextData:F,image:u(se),label:m,labelText:me,lineEnding:I,link:u(Y),listItem:u(),listOrdered:u(),listUnordered:u(),paragraph:u(),referenceString:Ee,resourceDestinationString:le,resourceTitleString:ge,resource:g,setextHeading:u($),setextHeadingLineSequence:N,setextHeadingText:B,strong:u(),thematicBreak:u()}};nr(n,(e||{}).mdastExtensions||[]);const t={};return i;function i(k){let C={type:"root",children:[],position:void 0};const R={stack:[C],tokenStack:[],config:n,enter:l,exit:c,buffer:s,resume:h,data:t},P=[],ee=[];let V=-1;for(;++V<k.length;)if(ee.push(k[V]),k[V][1].type==="listOrdered"||k[V][1].type==="listUnordered")if(k[V][0]==="enter")P.push(ee.length-1);else{const ne=P.pop();a(ee,ne)}for(k=ee,V=-1;++V<k.length;){const ne=n[k[V][0]];k[V][0]==="enter"&&n.beforeEnter.length>0&&r(n.beforeEnter,{...R,sliceSerialize:k[V][2].sliceSerialize},k[V][1]),er.call(ne,k[V][1].type)&&ne[k[V][1].type].call({...R,sliceSerialize:k[V][2].sliceSerialize},k[V][1]),k[V][0]==="exit"&&n.afterExit.length>0&&r(n.afterExit,{...R,sliceSerialize:k[V][2].sliceSerialize},k[V][1])}if(R.tokenStack.length>0){const ne=R.tokenStack[R.tokenStack.length-1];(ne[1]||$t).call(R,void 0,ne[0])}for(C.position={start:ke(k.length>0?k[0][1].start:{line:1,column:1,offset:0}),end:ke(k.length>0?k[k.length-2][1].end:{line:1,column:1,offset:0})},V=-1;++V<n.transforms.length;)C=n.transforms[V](C)||C;return C}function r(k,C,R){let P=-1;for(;++P<k.length;)k[P].call(C,R)}function a(k,C){const R=k.length-1;let P=C-1,ee=-1,V=!1,ne,de,Le,Oe;const Me=[];for(;++P<=R;){const re=k[P];switch(re[1].type){case"listUnordered":case"listOrdered":case"blockQuote":{re[0]==="enter"?ee++:ee--,Oe=void 0;break}case"lineEndingBlank":{re[0]==="enter"&&(ne&&!Oe&&!ee&&!Le&&(Le=P),Oe=void 0);break}case"linePrefix":case"listItemValue":case"listItemMarker":case"listItemPrefix":case"listItemPrefixWhitespace":break;default:Oe=void 0}if(!ee&&re[0]==="enter"&&re[1].type==="listItemPrefix"||ee===-1&&re[0]==="exit"&&(re[1].type==="listUnordered"||re[1].type==="listOrdered")){if(ne){let Ie=P;for(de=void 0;Ie--;){const ye=k[Ie];if(ye[1].type==="lineEnding"||ye[1].type==="lineEndingBlank"){if(ye[0]==="exit")continue;de&&(k[de][1].type="lineEndingBlank",V=!0),ye[1].type="lineEnding",de=Ie}else if(!(ye[1].type==="linePrefix"||ye[1].type==="blockQuotePrefix"||ye[1].type==="blockQuotePrefixWhitespace"||ye[1].type==="blockQuoteMarker"||ye[1].type==="listItemIndent"))break}Le&&(!de||Le<de)&&(ne._spread=!0),ne.end=Object.assign({},de?k[de][1].start:re[1].end),Me.push({at:de||P,event:["exit",ne,re[2]]})}if(re[1].type==="listItemPrefix"){const Ie={type:"listItem",_spread:!1,start:Object.assign({},re[1].start),end:void 0};ne=Ie,Me.push({at:P,event:["enter",Ie,re[2]]}),Le=void 0,Oe=!0}}}const Ft=k.splice(C);let kn=0;for(P=-1;++P<Ft.length;){for(;kn<Me.length&&Me[kn].at===C+P;)k.push(Me[kn++].event);k.push(Ft[P])}k[C][1]._spread=V}function o(k,C){return R;function R(P){l.call(this,k(P),P),C&&C.call(this,P)}}function s(){this.stack.push({type:"fragment",children:[]})}function l(k,C,R){this.stack[this.stack.length-1].children.push(k),this.stack.push(k),this.tokenStack.push([C,R||void 0]),k.position={start:ke(C.start),end:void 0}}function u(k){return C;function C(R){k&&k.call(this,R),c.call(this,R)}}function c(k,C){const R=this.stack.pop(),P=this.tokenStack.pop();if(!P)throw new Error("Cannot close `"+k.type+"` ("+Ue({start:k.start,end:k.end})+"): it’s not open");P[0].type!==k.type&&(C?C.call(this,k,P[0]):(P[1]||$t).call(this,k,P[0])),R.position.end=ke(k.end)}function h(){return ot(this.stack.pop())}function p(){this.data.expectingFirstListItemValue=!0}function d(k){if(this.data.expectingFirstListItemValue){const C=this.stack[this.stack.length-2];C.start=Number.parseInt(this.sliceSerialize(k),10),this.data.expectingFirstListItemValue=void 0}}function f(){const k=this.resume(),C=this.stack[this.stack.length-1];C.lang=k}function w(){const k=this.resume(),C=this.stack[this.stack.length-1];C.meta=k}function D(){this.data.flowCodeInside||(this.buffer(),this.data.flowCodeInside=!0)}function y(){const k=this.resume(),C=this.stack[this.stack.length-1];C.value=k.replace(/^(\r?\n|\r)|(\r?\n|\r)$/g,""),this.data.flowCodeInside=void 0}function _(){const k=this.resume(),C=this.stack[this.stack.length-1];C.value=k.replace(/(\r?\n|\r)$/g,"")}function x(k){const C=this.resume(),R=this.stack[this.stack.length-1];R.label=C,R.identifier=he(this.sliceSerialize(k)).toLowerCase()}function E(){const k=this.resume(),C=this.stack[this.stack.length-1];C.title=k}function S(){const k=this.resume(),C=this.stack[this.stack.length-1];C.url=k}function v(k){const C=this.stack[this.stack.length-1];if(!C.depth){const R=this.sliceSerialize(k).length;C.depth=R}}function B(){this.data.setextHeadingSlurpLineEnding=!0}function N(k){const C=this.stack[this.stack.length-1];C.depth=this.sliceSerialize(k).codePointAt(0)===61?1:2}function $(){this.data.setextHeadingSlurpLineEnding=void 0}function b(k){const R=this.stack[this.stack.length-1].children;let P=R[R.length-1];(!P||P.type!=="text")&&(P=Vr(),P.position={start:ke(k.start),end:void 0},R.push(P)),this.stack.push(P)}function F(k){const C=this.stack.pop();C.value+=this.sliceSerialize(k),C.position.end=ke(k.end)}function I(k){const C=this.stack[this.stack.length-1];if(this.data.atHardBreak){const R=C.children[C.children.length-1];R.position.end=ke(k.end),this.data.atHardBreak=void 0;return}!this.data.setextHeadingSlurpLineEnding&&n.canContainEols.includes(C.type)&&(b.call(this,k),F.call(this,k))}function H(){this.data.atHardBreak=!0}function W(){const k=this.resume(),C=this.stack[this.stack.length-1];C.value=k}function O(){const k=this.resume(),C=this.stack[this.stack.length-1];C.value=k}function J(){const k=this.resume(),C=this.stack[this.stack.length-1];C.value=k}function Y(){const k=this.stack[this.stack.length-1];if(this.data.inReference){const C=this.data.referenceType||"shortcut";k.type+="Reference",k.referenceType=C,delete k.url,delete k.title}else delete k.identifier,delete k.label;this.data.referenceType=void 0}function se(){const k=this.stack[this.stack.length-1];if(this.data.inReference){const C=this.data.referenceType||"shortcut";k.type+="Reference",k.referenceType=C,delete k.url,delete k.title}else delete k.identifier,delete k.label;this.data.referenceType=void 0}function me(k){const C=this.sliceSerialize(k),R=this.stack[this.stack.length-2];R.label=Ua(C),R.identifier=he(C).toLowerCase()}function m(){const k=this.stack[this.stack.length-1],C=this.resume(),R=this.stack[this.stack.length-1];if(this.data.inReference=!0,R.type==="link"){const P=k.children;R.children=P}else R.alt=C}function le(){const k=this.resume(),C=this.stack[this.stack.length-1];C.url=k}function ge(){const k=this.resume(),C=this.stack[this.stack.length-1];C.title=k}function g(){this.data.inReference=void 0}function ue(){this.data.referenceType="collapsed"}function Ee(k){const C=this.resume(),R=this.stack[this.stack.length-1];R.label=C,R.identifier=he(this.sliceSerialize(k)).toLowerCase(),this.data.referenceType="full"}function G(k){this.data.characterReferenceType=k.type}function ze(k){const C=this.sliceSerialize(k),R=this.data.characterReferenceType;let P;R?(P=Hi(C,R==="characterReferenceMarkerNumeric"?10:16),this.data.characterReferenceType=void 0):P=at(C);const ee=this.stack[this.stack.length-1];ee.value+=P}function be(k){const C=this.stack.pop();C.position.end=ke(k.end)}function Se(k){F.call(this,k);const C=this.stack[this.stack.length-1];C.url=this.sliceSerialize(k)}function Te(k){F.call(this,k);const C=this.stack[this.stack.length-1];C.url="mailto:"+this.sliceSerialize(k)}function bn(){return{type:"blockquote",children:[],position:void 0}}function vt(){return{type:"code",lang:null,meta:null,value:"",position:void 0}}function Lr(){return{type:"inlineCode",value:"",position:void 0}}function Or(){return{type:"definition",identifier:"",label:null,title:null,url:"",position:void 0}}function Mr(){return{type:"emphasis",children:[],position:void 0}}function Dt(){return{type:"heading",depth:0,children:[],position:void 0}}function xt(){return{type:"break",position:void 0}}function _t(){return{type:"html",value:"",position:void 0}}function Nr(){return{type:"image",title:null,url:"",alt:null,position:void 0}}function At(){return{type:"link",title:null,url:"",children:[],position:void 0}}function Ct(k){return{type:"list",ordered:k.type==="listOrdered",start:null,spread:k._spread,children:[],position:void 0}}function Hr(k){return{type:"listItem",spread:k._spread,checked:null,children:[],position:void 0}}function jr(){return{type:"paragraph",children:[],position:void 0}}function Ur(){return{type:"strong",children:[],position:void 0}}function Vr(){return{type:"text",value:"",position:void 0}}function Wr(){return{type:"thematicBreak",position:void 0}}}function ke(e){return{line:e.line,column:e.column,offset:e.offset}}function nr(e,n){let t=-1;for(;++t<n.length;){const i=n[t];Array.isArray(i)?nr(e,i):Ka(e,i)}}function Ka(e,n){let t;for(t in n)if(er.call(n,t))switch(t){case"canContainEols":{const i=n[t];i&&e[t].push(...i);break}case"transforms":{const i=n[t];i&&e[t].push(...i);break}case"afterExit":case"beforeEnter":{const i=n[t];i&&e[t].push(i);break}case"enter":case"exit":{const i=n[t];i&&Object.assign(e[t],i);break}}}function $t(e,n){throw e?new Error("Cannot close `"+e.type+"` ("+Ue({start:e.start,end:e.end})+"): a different token (`"+n.type+"`, "+Ue({start:n.start,end:n.end})+") is open"):new Error("Cannot close document, a token (`"+n.type+"`, "+Ue({start:n.start,end:n.end})+") is still open")}function Ga(e){const n=this;n.parser=t;function t(i){return Wa(i,{...n.data("settings"),...e,extensions:n.data("micromarkExtensions")||[],mdastExtensions:n.data("fromMarkdownExtensions")||[]})}}function Ya(e,n){const t={type:"element",tagName:"blockquote",properties:{},children:e.wrap(e.all(n),!0)};return e.patch(n,t),e.applyData(n,t)}function Qa(e,n){const t={type:"element",tagName:"br",properties:{},children:[]};return e.patch(n,t),[e.applyData(n,t),{type:"text",value:`
`}]}function Xa(e,n){const t=n.value?n.value+`
`:"",i={},r=n.lang?n.lang.split(/\s+/):[];r.length>0&&(i.className=["language-"+r[0]]);let a={type:"element",tagName:"code",properties:i,children:[{type:"text",value:t}]};return n.meta&&(a.data={meta:n.meta}),e.patch(n,a),a=e.applyData(n,a),a={type:"element",tagName:"pre",properties:{},children:[a]},e.patch(n,a),a}function Ja(e,n){const t={type:"element",tagName:"del",properties:{},children:e.all(n)};return e.patch(n,t),e.applyData(n,t)}function Za(e,n){const t={type:"element",tagName:"em",properties:{},children:e.all(n)};return e.patch(n,t),e.applyData(n,t)}function es(e,n){const t=typeof e.options.clobberPrefix=="string"?e.options.clobberPrefix:"user-content-",i=String(n.identifier).toUpperCase(),r=Pe(i.toLowerCase()),a=e.footnoteOrder.indexOf(i);let o,s=e.footnoteCounts.get(i);s===void 0?(s=0,e.footnoteOrder.push(i),o=e.footnoteOrder.length):o=a+1,s+=1,e.footnoteCounts.set(i,s);const l={type:"element",tagName:"a",properties:{href:"#"+t+"fn-"+r,id:t+"fnref-"+r+(s>1?"-"+s:""),dataFootnoteRef:!0,ariaDescribedBy:["footnote-label"]},children:[{type:"text",value:String(o)}]};e.patch(n,l);const u={type:"element",tagName:"sup",properties:{},children:[l]};return e.patch(n,u),e.applyData(n,u)}function ns(e,n){const t={type:"element",tagName:"h"+n.depth,properties:{},children:e.all(n)};return e.patch(n,t),e.applyData(n,t)}function ts(e,n){if(e.options.allowDangerousHtml){const t={type:"raw",value:n.value};return e.patch(n,t),e.applyData(n,t)}}function tr(e,n){const t=n.referenceType;let i="]";if(t==="collapsed"?i+="[]":t==="full"&&(i+="["+(n.label||n.identifier)+"]"),n.type==="imageReference")return[{type:"text",value:"!["+n.alt+i}];const r=e.all(n),a=r[0];a&&a.type==="text"?a.value="["+a.value:r.unshift({type:"text",value:"["});const o=r[r.length-1];return o&&o.type==="text"?o.value+=i:r.push({type:"text",value:i}),r}function is(e,n){const t=String(n.identifier).toUpperCase(),i=e.definitionById.get(t);if(!i)return tr(e,n);const r={src:Pe(i.url||""),alt:n.alt};i.title!==null&&i.title!==void 0&&(r.title=i.title);const a={type:"element",tagName:"img",properties:r,children:[]};return e.patch(n,a),e.applyData(n,a)}function rs(e,n){const t={src:Pe(n.url)};n.alt!==null&&n.alt!==void 0&&(t.alt=n.alt),n.title!==null&&n.title!==void 0&&(t.title=n.title);const i={type:"element",tagName:"img",properties:t,children:[]};return e.patch(n,i),e.applyData(n,i)}function os(e,n){const t={type:"text",value:n.value.replace(/\r?\n|\r/g," ")};e.patch(n,t);const i={type:"element",tagName:"code",properties:{},children:[t]};return e.patch(n,i),e.applyData(n,i)}function as(e,n){const t=String(n.identifier).toUpperCase(),i=e.definitionById.get(t);if(!i)return tr(e,n);const r={href:Pe(i.url||"")};i.title!==null&&i.title!==void 0&&(r.title=i.title);const a={type:"element",tagName:"a",properties:r,children:e.all(n)};return e.patch(n,a),e.applyData(n,a)}function ss(e,n){const t={href:Pe(n.url)};n.title!==null&&n.title!==void 0&&(t.title=n.title);const i={type:"element",tagName:"a",properties:t,children:e.all(n)};return e.patch(n,i),e.applyData(n,i)}function ls(e,n,t){const i=e.all(n),r=t?us(t):ir(n),a={},o=[];if(typeof n.checked=="boolean"){const c=i[0];let h;c&&c.type==="element"&&c.tagName==="p"?h=c:(h={type:"element",tagName:"p",properties:{},children:[]},i.unshift(h)),h.children.length>0&&h.children.unshift({type:"text",value:" "}),h.children.unshift({type:"element",tagName:"input",properties:{type:"checkbox",checked:n.checked,disabled:!0},children:[]}),a.className=["task-list-item"]}let s=-1;for(;++s<i.length;){const c=i[s];(r||s!==0||c.type!=="element"||c.tagName!=="p")&&o.push({type:"text",value:`
`}),c.type==="element"&&c.tagName==="p"&&!r?o.push(...c.children):o.push(c)}const l=i[i.length-1];l&&(r||l.type!=="element"||l.tagName!=="p")&&o.push({type:"text",value:`
`});const u={type:"element",tagName:"li",properties:a,children:o};return e.patch(n,u),e.applyData(n,u)}function us(e){let n=!1;if(e.type==="list"){n=e.spread||!1;const t=e.children;let i=-1;for(;!n&&++i<t.length;)n=ir(t[i])}return n}function ir(e){const n=e.spread;return n??e.children.length>1}function cs(e,n){const t={},i=e.all(n);let r=-1;for(typeof n.start=="number"&&n.start!==1&&(t.start=n.start);++r<i.length;){const o=i[r];if(o.type==="element"&&o.tagName==="li"&&o.properties&&Array.isArray(o.properties.className)&&o.properties.className.includes("task-list-item")){t.className=["contains-task-list"];break}}const a={type:"element",tagName:n.ordered?"ol":"ul",properties:t,children:e.wrap(i,!0)};return e.patch(n,a),e.applyData(n,a)}function hs(e,n){const t={type:"element",tagName:"p",properties:{},children:e.all(n)};return e.patch(n,t),e.applyData(n,t)}function ds(e,n){const t={type:"root",children:e.wrap(e.all(n))};return e.patch(n,t),e.applyData(n,t)}function ps(e,n){const t={type:"element",tagName:"strong",properties:{},children:e.all(n)};return e.patch(n,t),e.applyData(n,t)}function fs(e,n){const t=e.all(n),i=t.shift(),r=[];if(i){const o={type:"element",tagName:"thead",properties:{},children:e.wrap([i],!0)};e.patch(n.children[0],o),r.push(o)}if(t.length>0){const o={type:"element",tagName:"tbody",properties:{},children:e.wrap(t,!0)},s=nt(n.children[1]),l=qi(n.children[n.children.length-1]);s&&l&&(o.position={start:s,end:l}),r.push(o)}const a={type:"element",tagName:"table",properties:{},children:e.wrap(r,!0)};return e.patch(n,a),e.applyData(n,a)}function ms(e,n,t){const i=t?t.children:void 0,a=(i?i.indexOf(n):1)===0?"th":"td",o=t&&t.type==="table"?t.align:void 0,s=o?o.length:n.children.length;let l=-1;const u=[];for(;++l<s;){const h=n.children[l],p={},d=o?o[l]:void 0;d&&(p.align=d);let f={type:"element",tagName:a,properties:p,children:[]};h&&(f.children=e.all(h),e.patch(h,f),f=e.applyData(h,f)),u.push(f)}const c={type:"element",tagName:"tr",properties:{},children:e.wrap(u,!0)};return e.patch(n,c),e.applyData(n,c)}function gs(e,n){const t={type:"element",tagName:"td",properties:{},children:e.all(n)};return e.patch(n,t),e.applyData(n,t)}const Kt=9,Gt=32;function ys(e){const n=String(e),t=/\r?\n|\r/g;let i=t.exec(n),r=0;const a=[];for(;i;)a.push(Yt(n.slice(r,i.index),r>0,!0),i[0]),r=i.index+i[0].length,i=t.exec(n);return a.push(Yt(n.slice(r),r>0,!1)),a.join("")}function Yt(e,n,t){let i=0,r=e.length;if(n){let a=e.codePointAt(i);for(;a===Kt||a===Gt;)i++,a=e.codePointAt(i)}if(t){let a=e.codePointAt(r-1);for(;a===Kt||a===Gt;)r--,a=e.codePointAt(r-1)}return r>i?e.slice(i,r):""}function ws(e,n){const t={type:"text",value:ys(String(n.value))};return e.patch(n,t),e.applyData(n,t)}function bs(e,n){const t={type:"element",tagName:"hr",properties:{},children:[]};return e.patch(n,t),e.applyData(n,t)}const ks={blockquote:Ya,break:Qa,code:Xa,delete:Ja,emphasis:Za,footnoteReference:es,heading:ns,html:ts,imageReference:is,image:rs,inlineCode:os,linkReference:as,link:ss,listItem:ls,list:cs,paragraph:hs,root:ds,strong:ps,table:fs,tableCell:gs,tableRow:ms,text:ws,thematicBreak:bs,toml:Xe,yaml:Xe,definition:Xe,footnoteDefinition:Xe};function Xe(){}const rr=-1,fn=0,We=1,un=2,lt=3,ut=4,ct=5,ht=6,or=7,ar=8,{defineProperty:vs}=Object,sr=typeof self=="object"?self:globalThis,Qt=(e,n)=>{switch(e){case"Function":case"SharedWorker":case"Worker":case"eval":case"setInterval":case"setTimeout":throw new TypeError("unable to deserialize "+e)}return new sr[e](n)},Ds=(e,n)=>{const t=(r,a)=>(e.set(a,r),r),i=r=>{if(e.has(r))return e.get(r);const[a,o]=n[r];switch(a){case fn:case rr:return t(o,r);case We:{const s=t([],r);for(const l of o)s.push(i(l));return s}case un:{const s=t({},r);for(const[l,u]of o){const c=i(l),h=i(u);c==="__proto__"?vs(s,c,{value:h,configurable:!0,enumerable:!0,writable:!0}):s[c]=h}return s}case lt:return t(new Date(o),r);case ut:{const{source:s,flags:l}=o;return t(new RegExp(s,l),r)}case ct:{const s=t(new Map,r);for(const[l,u]of o)s.set(i(l),i(u));return s}case ht:{const s=t(new Set,r);for(const l of o)s.add(i(l));return s}case or:{const{name:s,message:l}=o;return t(typeof sr[s]=="function"?Qt(s,l):new Error(l),r)}case ar:return t(BigInt(o),r);case"BigInt":return t(Object(BigInt(o)),r);case"ArrayBuffer":return t(new Uint8Array(o).buffer,o);case"DataView":{const{buffer:s}=new Uint8Array(o);return t(new DataView(s),o)}case"-0":return-0}return t(Qt(a,o),r)};return i},Xt=e=>Ds(new Map,e)(0),_e="",{toString:xs}={},{keys:_s,is:As}=Object,je=e=>{const n=typeof e;if(n!=="object"||!e)return[fn,n];const t=xs.call(e).slice(8,-1);switch(t){case"Array":return[We,_e];case"Object":return[un,_e];case"Date":return[lt,_e];case"RegExp":return[ut,_e];case"Map":return[ct,_e];case"Set":return[ht,_e];case"DataView":return[We,t]}return t.includes("Array")?[We,t]:e instanceof Error?[or,e.name||"Error"]:[un,t]},Je=([e,n])=>e===fn&&(n==="function"||n==="symbol"),Cs=(e,n,t,i)=>{const r=(o,s)=>{const l=i.push(o)-1;return t.set(s,l),l},a=o=>{if(t.has(o))return t.get(o);let[s,l]=je(o);switch(s){case fn:{let c=o;switch(l){case"bigint":s=ar,c=o.toString();break;case"number":if(!o&&As(o,-0))return i.push(["-0"])-1;break;case"function":case"symbol":if(e)throw new TypeError("unable to serialize "+l);c=null;break;case"undefined":return r([rr],o)}return r([s,c],o)}case We:{if(l){let p=o;return l==="DataView"?p=new Uint8Array(o.buffer):l==="ArrayBuffer"&&(p=new Uint8Array(o)),r([l,[...p]],o)}const c=[],h=r([s,c],o);for(const p of o)c.push(a(p));return h}case un:{if(l)switch(l){case"BigInt":return r([l,o.toString()],o);case"Boolean":case"Number":case"String":return r([l,o.valueOf()],o)}if(n&&"toJSON"in o)return a(o.toJSON());const c=[],h=r([s,c],o);for(const p of _s(o))(e||!Je(je(o[p])))&&c.push([a(p),a(o[p])]);return h}case lt:return r([s,isNaN(o.getTime())?_e:o.toISOString()],o);case ut:{const{source:c,flags:h}=o;return r([s,{source:c,flags:h}],o)}case ct:{const c=[],h=r([s,c],o);for(const[p,d]of o)(e||!(Je(je(p))||Je(je(d))))&&c.push([a(p),a(d)]);return h}case ht:{const c=[],h=r([s,c],o);for(const p of o)(e||!Je(je(p)))&&c.push(a(p));return h}}const{message:u}=o;return r([s,{name:l,message:u}],o)};return a},Jt=(e,{json:n,lossy:t}={})=>{const i=[];return Cs(!(n||t),!!n,new Map,i)(e),i},cn=typeof structuredClone=="function"?(e,n)=>n&&("json"in n||"lossy"in n)?Xt(Jt(e,n)):structuredClone(e):(e,n)=>Xt(Jt(e,n));function Fs(e,n){const t=[{type:"text",value:"↩"}];return n>1&&t.push({type:"element",tagName:"sup",properties:{},children:[{type:"text",value:String(n)}]}),t}function Es(e,n){return"Back to reference "+(e+1)+(n>1?"-"+n:"")}function Ss(e){const n=typeof e.options.clobberPrefix=="string"?e.options.clobberPrefix:"user-content-",t=e.options.footnoteBackContent||Fs,i=e.options.footnoteBackLabel||Es,r=e.options.footnoteLabel||"Footnotes",a=e.options.footnoteLabelTagName||"h2",o=e.options.footnoteLabelProperties||{className:["sr-only"]},s=[];let l=-1;for(;++l<e.footnoteOrder.length;){const u=e.footnoteById.get(e.footnoteOrder[l]);if(!u)continue;const c=e.all(u),h=String(u.identifier).toUpperCase(),p=Pe(h.toLowerCase());let d=0;const f=[],w=e.footnoteCounts.get(h);for(;w!==void 0&&++d<=w;){f.length>0&&f.push({type:"text",value:" "});let _=typeof t=="string"?t:t(l,d);typeof _=="string"&&(_={type:"text",value:_}),f.push({type:"element",tagName:"a",properties:{href:"#"+n+"fnref-"+p+(d>1?"-"+d:""),dataFootnoteBackref:"",ariaLabel:typeof i=="string"?i:i(l,d),className:["data-footnote-backref"]},children:Array.isArray(_)?_:[_]})}const D=c[c.length-1];if(D&&D.type==="element"&&D.tagName==="p"){const _=D.children[D.children.length-1];_&&_.type==="text"?_.value+=" ":D.children.push({type:"text",value:" "}),D.children.push(...f)}else c.push(...f);const y={type:"element",tagName:"li",properties:{id:n+"fn-"+p},children:e.wrap(c,!0)};e.patch(u,y),s.push(y)}if(s.length!==0)return{type:"element",tagName:"section",properties:{dataFootnotes:!0,className:["footnotes"]},children:[{type:"element",tagName:a,properties:{...cn(o),id:"footnote-label"},children:[{type:"text",value:r}]},{type:"text",value:`
`},{type:"element",tagName:"ol",properties:{},children:e.wrap(s,!0)},{type:"text",value:`
`}]}}const mn=function(e){if(e==null)return qs;if(typeof e=="function")return gn(e);if(typeof e=="object")return Array.isArray(e)?Ts(e):Is(e);if(typeof e=="string")return Bs(e);throw new Error("Expected function, string, or object as test")};function Ts(e){const n=[];let t=-1;for(;++t<e.length;)n[t]=mn(e[t]);return gn(i);function i(...r){let a=-1;for(;++a<n.length;)if(n[a].apply(this,r))return!0;return!1}}function Is(e){const n=e;return gn(t);function t(i){const r=i;let a;for(a in e)if(r[a]!==n[a])return!1;return!0}}function Bs(e){return gn(n);function n(t){return t&&t.type===e}}function gn(e){return n;function n(t,i,r){return!!(Rs(t)&&e.call(this,t,typeof i=="number"?i:void 0,r||void 0))}}function qs(){return!0}function Rs(e){return e!==null&&typeof e=="object"&&"type"in e}const lr=[],Ps=!0,on=!1,$n="skip";function Kn(e,n,t,i){if(!e||typeof e!="object")throw new Error("Unexpected value `"+e+"` for `tree`, expected node");let r=!0,a,o,s,l;if(typeof t=="function"||t&&typeof t=="object"?(a=n,o=t,i&&(r=!1)):(o=n,t&&(r=!1)),typeof o=="function")s=o;else if(o&&typeof o=="object"){if(!(o.enter===null||o.enter===void 0))if(typeof o.enter=="function")s=o.enter;else throw new Error("Unexpected value `"+o.enter+"` for `visitors.enter`, expected optional visitor");if(typeof o.exit=="function")l=o.exit;else throw new Error("Unexpected value `"+o.exit+"` for `visitors.exit`, expected visitor (pass a visitor directly if you only want an enter visitor)")}else throw new Error("Unexpected value `"+o+"` for `enter` or `visitors`, expected visitor or object with visitors");const u=mn(a),c=r?1:-1;h(e,void 0,[])();function h(p,d,f){const w=p&&typeof p=="object"?p:{};if(typeof w.type=="string"){const y=typeof w.tagName=="string"?w.tagName:typeof w.name=="string"?w.name:void 0;Object.defineProperty(D,"name",{value:"node ("+(p.type+(y?"<"+y+">":""))+")"})}return D;function D(){const y=!a||u(p,d,f[f.length-1]||void 0);let _=lr;if(s&&y&&(_=Zt(s(p,f,d)),_[0]===on))return _;if("children"in p&&p.children){const x=p;if(x.children&&_[0]!==$n){let E=(r?-1:x.children.length)+c;const S=[...f,x];for(;E>-1&&E<x.children.length;){const v=x.children[E],B=h(v,E,S)();if(B[0]===on)return B;E=typeof B[1]=="number"?B[1]:E+c}}}if(l&&y){const x=Zt(l(p,f,d));if(x[0]===$n)throw new Error("Unexpected value `"+x[0]+"` from `exit`, expected `CONTINUE`, `EXIT`, index, or nothing");if(x[0]===on||typeof x[1]=="number")return x}return _}}}function Zt(e){return Array.isArray(e)?e:typeof e=="number"?[Ps,e]:e==null?lr:[e]}function yn(e,n,t,i){let r,a,o;typeof t=="function"||t&&typeof t=="object"?(r=n,a=t,o=i):(a=n,o=t),typeof a=="function"?Kn(e,r,Gn(a),o):Kn(e,r,zs(a),o)}function zs(e){return!e||typeof e!="object"?e:{enter:typeof e.enter=="function"?Gn(e.enter):e.enter,exit:typeof e.exit=="function"?Gn(e.exit):e.exit}}function Gn(e){return n;function n(t,i,r){return e(t,r,i[i.length-1])}}const Yn={}.hasOwnProperty,Ls={};function Os(e,n){const t=n||Ls,i=new Map,r=new Map,a=new Map,o={...ks,...t.handlers},s={all:u,applyData:Ns,definitionById:i,footnoteById:r,footnoteCounts:a,footnoteOrder:[],handlers:o,one:l,options:t,patch:Ms,wrap:js};return yn(e,function(c){if(c.type==="definition"||c.type==="footnoteDefinition"){const h=c.type==="definition"?i:r,p=String(c.identifier).toUpperCase();h.has(p)||h.set(p,c)}}),s;function l(c,h){const p=c.type,d=s.handlers[p];if(Yn.call(s.handlers,p)&&d)return d(s,c,h);if(s.options.passThrough&&s.options.passThrough.includes(p)){if("children"in c){const{children:w,...D}=c,y=cn(D);return y.children=s.all(c),y}return cn(c)}return(s.options.unknownHandler||Hs)(s,c,h)}function u(c){const h=[];if("children"in c){const p=c.children;let d=-1;for(;++d<p.length;){const f=s.one(p[d],c);if(f){if(d&&p[d-1].type==="break"&&(!Array.isArray(f)&&f.type==="text"&&(f.value=ei(f.value)),!Array.isArray(f)&&f.type==="element")){const w=f.children[0];w&&w.type==="text"&&(w.value=ei(w.value))}Array.isArray(f)?h.push(...f):h.push(f)}}}return h}}function Ms(e,n){e.position&&(n.position=F0(e))}function Ns(e,n){let t=n;if(e&&e.data){const i=e.data.hName,r=e.data.hChildren,a=e.data.hProperties;if(typeof i=="string")if(t.type==="element")t.tagName=i;else{const o="children"in t?t.children:[t];t={type:"element",tagName:i,properties:{},children:o}}t.type==="element"&&a&&Object.assign(t.properties,cn(a)),"children"in t&&t.children&&r!==null&&r!==void 0&&(t.children=r)}return t}function Hs(e,n){const t=n.data||{},i="value"in n&&!(Yn.call(t,"hProperties")||Yn.call(t,"hChildren"))?{type:"text",value:n.value}:{type:"element",tagName:"div",properties:{},children:e.all(n)};return e.patch(n,i),e.applyData(n,i)}function js(e,n){const t=[];let i=-1;for(n&&t.push({type:"text",value:`
`});++i<e.length;)i&&t.push({type:"text",value:`
`}),t.push(e[i]);return n&&e.length>0&&t.push({type:"text",value:`
`}),t}function ei(e){let n=0,t=e.charCodeAt(n);for(;t===9||t===32;)n++,t=e.charCodeAt(n);return e.slice(n)}function ni(e,n){const t=Os(e,n),i=t.one(e,void 0),r=Ss(t),a=Array.isArray(i)?{type:"root",children:i}:i||{type:"root",children:[]};return r&&a.children.push({type:"text",value:`
`},r),a}function Us(e,n){return e&&"run"in e?async function(t,i){const r=ni(t,{file:i,...n});await e.run(r,i)}:function(t,i){return ni(t,{file:i,...e||n})}}function ti(e){if(e)throw e}var an=Object.prototype.hasOwnProperty,ur=Object.prototype.toString,ii=Object.defineProperty,ri=Object.getOwnPropertyDescriptor,oi=function(n){return typeof Array.isArray=="function"?Array.isArray(n):ur.call(n)==="[object Array]"},ai=function(n){if(!n||ur.call(n)!=="[object Object]")return!1;var t=an.call(n,"constructor"),i=n.constructor&&n.constructor.prototype&&an.call(n.constructor.prototype,"isPrototypeOf");if(n.constructor&&!t&&!i)return!1;var r;for(r in n);return typeof r>"u"||an.call(n,r)},si=function(n,t){ii&&t.name==="__proto__"?ii(n,t.name,{enumerable:!0,configurable:!0,value:t.newValue,writable:!0}):n[t.name]=t.newValue},li=function(n,t){if(t==="__proto__")if(an.call(n,t)){if(ri)return ri(n,t).value}else return;return n[t]},Vs=function e(){var n,t,i,r,a,o,s=arguments[0],l=1,u=arguments.length,c=!1;for(typeof s=="boolean"&&(c=s,s=arguments[1]||{},l=2),(s==null||typeof s!="object"&&typeof s!="function")&&(s={});l<u;++l)if(n=arguments[l],n!=null)for(t in n)i=li(s,t),r=li(n,t),s!==r&&(c&&r&&(ai(r)||(a=oi(r)))?(a?(a=!1,o=i&&oi(i)?i:[]):o=i&&ai(i)?i:{},si(s,{name:t,newValue:e(c,o,r)})):typeof r<"u"&&si(s,{name:t,newValue:r}));return s};const Cn=$r(Vs);function Qn(e){if(typeof e!="object"||e===null)return!1;const n=Object.getPrototypeOf(e);return(n===null||n===Object.prototype||Object.getPrototypeOf(n)===null)&&!(Symbol.toStringTag in e)&&!(Symbol.iterator in e)}function Ws(){const e=[],n={run:t,use:i};return n;function t(...r){let a=-1;const o=r.pop();if(typeof o!="function")throw new TypeError("Expected function as last argument, not "+o);s(null,...r);function s(l,...u){const c=e[++a];let h=-1;if(l){o(l);return}for(;++h<r.length;)(u[h]===null||u[h]===void 0)&&(u[h]=r[h]);r=u,c?$s(c,s)(...u):o(null,...u)}}function i(r){if(typeof r!="function")throw new TypeError("Expected `middelware` to be a function, not "+r);return e.push(r),n}}function $s(e,n){let t;return i;function i(...o){const s=e.length>o.length;let l;s&&o.push(r);try{l=e.apply(this,o)}catch(u){const c=u;if(s&&t)throw c;return r(c)}s||(l&&l.then&&typeof l.then=="function"?l.then(a,r):l instanceof Error?r(l):a(l))}function r(o,...s){t||(t=!0,n(o,...s))}function a(o){r(null,o)}}const pe={basename:Ks,dirname:Gs,extname:Ys,join:Qs,sep:"/"};function Ks(e,n){if(n!==void 0&&typeof n!="string")throw new TypeError('"ext" argument must be a string');Ye(e);let t=0,i=-1,r=e.length,a;if(n===void 0||n.length===0||n.length>e.length){for(;r--;)if(e.codePointAt(r)===47){if(a){t=r+1;break}}else i<0&&(a=!0,i=r+1);return i<0?"":e.slice(t,i)}if(n===e)return"";let o=-1,s=n.length-1;for(;r--;)if(e.codePointAt(r)===47){if(a){t=r+1;break}}else o<0&&(a=!0,o=r+1),s>-1&&(e.codePointAt(r)===n.codePointAt(s--)?s<0&&(i=r):(s=-1,i=o));return t===i?i=o:i<0&&(i=e.length),e.slice(t,i)}function Gs(e){if(Ye(e),e.length===0)return".";let n=-1,t=e.length,i;for(;--t;)if(e.codePointAt(t)===47){if(i){n=t;break}}else i||(i=!0);return n<0?e.codePointAt(0)===47?"/":".":n===1&&e.codePointAt(0)===47?"//":e.slice(0,n)}function Ys(e){Ye(e);let n=e.length,t=-1,i=0,r=-1,a=0,o;for(;n--;){const s=e.codePointAt(n);if(s===47){if(o){i=n+1;break}continue}t<0&&(o=!0,t=n+1),s===46?r<0?r=n:a!==1&&(a=1):r>-1&&(a=-1)}return r<0||t<0||a===0||a===1&&r===t-1&&r===i+1?"":e.slice(r,t)}function Qs(...e){let n=-1,t;for(;++n<e.length;)Ye(e[n]),e[n]&&(t=t===void 0?e[n]:t+"/"+e[n]);return t===void 0?".":Xs(t)}function Xs(e){Ye(e);const n=e.codePointAt(0)===47;let t=Js(e,!n);return t.length===0&&!n&&(t="."),t.length>0&&e.codePointAt(e.length-1)===47&&(t+="/"),n?"/"+t:t}function Js(e,n){let t="",i=0,r=-1,a=0,o=-1,s,l;for(;++o<=e.length;){if(o<e.length)s=e.codePointAt(o);else{if(s===47)break;s=47}if(s===47){if(!(r===o-1||a===1))if(r!==o-1&&a===2){if(t.length<2||i!==2||t.codePointAt(t.length-1)!==46||t.codePointAt(t.length-2)!==46){if(t.length>2){if(l=t.lastIndexOf("/"),l!==t.length-1){l<0?(t="",i=0):(t=t.slice(0,l),i=t.length-1-t.lastIndexOf("/")),r=o,a=0;continue}}else if(t.length>0){t="",i=0,r=o,a=0;continue}}n&&(t=t.length>0?t+"/..":"..",i=2)}else t.length>0?t+="/"+e.slice(r+1,o):t=e.slice(r+1,o),i=o-r-1;r=o,a=0}else s===46&&a>-1?a++:a=-1}return t}function Ye(e){if(typeof e!="string")throw new TypeError("Path must be a string. Received "+JSON.stringify(e))}const Zs={cwd:el};function el(){return"/"}function Xn(e){return!!(e!==null&&typeof e=="object"&&"href"in e&&e.href&&"protocol"in e&&e.protocol&&e.auth===void 0)}function nl(e){if(typeof e=="string")e=new URL(e);else if(!Xn(e)){const n=new TypeError('The "path" argument must be of type string or an instance of URL. Received `'+e+"`");throw n.code="ERR_INVALID_ARG_TYPE",n}if(e.protocol!=="file:"){const n=new TypeError("The URL must be of scheme file");throw n.code="ERR_INVALID_URL_SCHEME",n}return tl(e)}function tl(e){if(e.hostname!==""){const i=new TypeError('File URL host must be "localhost" or empty on darwin');throw i.code="ERR_INVALID_FILE_URL_HOST",i}const n=e.pathname;let t=-1;for(;++t<n.length;)if(n.codePointAt(t)===37&&n.codePointAt(t+1)===50){const i=n.codePointAt(t+2);if(i===70||i===102){const r=new TypeError("File URL path must not include encoded / characters");throw r.code="ERR_INVALID_FILE_URL_PATH",r}}return decodeURIComponent(n)}const Fn=["history","path","basename","stem","extname","dirname"];class cr{constructor(n){let t;n?Xn(n)?t={path:n}:typeof n=="string"||il(n)?t={value:n}:t=n:t={},this.cwd="cwd"in t?"":Zs.cwd(),this.data={},this.history=[],this.messages=[],this.value,this.map,this.result,this.stored;let i=-1;for(;++i<Fn.length;){const a=Fn[i];a in t&&t[a]!==void 0&&t[a]!==null&&(this[a]=a==="history"?[...t[a]]:t[a])}let r;for(r in t)Fn.includes(r)||(this[r]=t[r])}get basename(){return typeof this.path=="string"?pe.basename(this.path):void 0}set basename(n){Sn(n,"basename"),En(n,"basename"),this.path=pe.join(this.dirname||"",n)}get dirname(){return typeof this.path=="string"?pe.dirname(this.path):void 0}set dirname(n){ui(this.basename,"dirname"),this.path=pe.join(n||"",this.basename)}get extname(){return typeof this.path=="string"?pe.extname(this.path):void 0}set extname(n){if(En(n,"extname"),ui(this.dirname,"extname"),n){if(n.codePointAt(0)!==46)throw new Error("`extname` must start with `.`");if(n.includes(".",1))throw new Error("`extname` cannot contain multiple dots")}this.path=pe.join(this.dirname,this.stem+(n||""))}get path(){return this.history[this.history.length-1]}set path(n){Xn(n)&&(n=nl(n)),Sn(n,"path"),this.path!==n&&this.history.push(n)}get stem(){return typeof this.path=="string"?pe.basename(this.path,this.extname):void 0}set stem(n){Sn(n,"stem"),En(n,"stem"),this.path=pe.join(this.dirname||"",n+(this.extname||""))}fail(n,t,i){const r=this.message(n,t,i);throw r.fatal=!0,r}info(n,t,i){const r=this.message(n,t,i);return r.fatal=void 0,r}message(n,t,i){const r=new Z(n,t,i);return this.path&&(r.name=this.path+":"+r.name,r.file=this.path),r.fatal=!1,this.messages.push(r),r}toString(n){return this.value===void 0?"":typeof this.value=="string"?this.value:new TextDecoder(n||void 0).decode(this.value)}}function En(e,n){if(e&&e.includes(pe.sep))throw new Error("`"+n+"` cannot be a path: did not expect `"+pe.sep+"`")}function Sn(e,n){if(!e)throw new Error("`"+n+"` cannot be empty")}function ui(e,n){if(!e)throw new Error("Setting `"+n+"` requires `path` to be set too")}function il(e){return!!(e&&typeof e=="object"&&"byteLength"in e&&"byteOffset"in e)}const rl=function(e){const i=this.constructor.prototype,r=i[e],a=function(){return r.apply(a,arguments)};return Object.setPrototypeOf(a,i),a},ol={}.hasOwnProperty;class dt extends rl{constructor(){super("copy"),this.Compiler=void 0,this.Parser=void 0,this.attachers=[],this.compiler=void 0,this.freezeIndex=-1,this.frozen=void 0,this.namespace={},this.parser=void 0,this.transformers=Ws()}copy(){const n=new dt;let t=-1;for(;++t<this.attachers.length;){const i=this.attachers[t];n.use(...i)}return n.data(Cn(!0,{},this.namespace)),n}data(n,t){return typeof n=="string"?arguments.length===2?(Bn("data",this.frozen),this.namespace[n]=t,this):ol.call(this.namespace,n)&&this.namespace[n]||void 0:n?(Bn("data",this.frozen),this.namespace=n,this):this.namespace}freeze(){if(this.frozen)return this;const n=this;for(;++this.freezeIndex<this.attachers.length;){const[t,...i]=this.attachers[this.freezeIndex];if(i[0]===!1)continue;i[0]===!0&&(i[0]=void 0);const r=t.call(n,...i);typeof r=="function"&&this.transformers.use(r)}return this.frozen=!0,this.freezeIndex=Number.POSITIVE_INFINITY,this}parse(n){this.freeze();const t=Ze(n),i=this.parser||this.Parser;return Tn("parse",i),i(String(t),t)}process(n,t){const i=this;return this.freeze(),Tn("process",this.parser||this.Parser),In("process",this.compiler||this.Compiler),t?r(void 0,t):new Promise(r);function r(a,o){const s=Ze(n),l=i.parse(s);i.run(l,s,function(c,h,p){if(c||!h||!p)return u(c);const d=h,f=i.stringify(d,p);ll(f)?p.value=f:p.result=f,u(c,p)});function u(c,h){c||!h?o(c):a?a(h):t(void 0,h)}}}processSync(n){let t=!1,i;return this.freeze(),Tn("processSync",this.parser||this.Parser),In("processSync",this.compiler||this.Compiler),this.process(n,r),hi("processSync","process",t),i;function r(a,o){t=!0,ti(a),i=o}}run(n,t,i){ci(n),this.freeze();const r=this.transformers;return!i&&typeof t=="function"&&(i=t,t=void 0),i?a(void 0,i):new Promise(a);function a(o,s){const l=Ze(t);r.run(n,l,u);function u(c,h,p){const d=h||n;c?s(c):o?o(d):i(void 0,d,p)}}}runSync(n,t){let i=!1,r;return this.run(n,t,a),hi("runSync","run",i),r;function a(o,s){ti(o),r=s,i=!0}}stringify(n,t){this.freeze();const i=Ze(t),r=this.compiler||this.Compiler;return In("stringify",r),ci(n),r(n,i)}use(n,...t){const i=this.attachers,r=this.namespace;if(Bn("use",this.frozen),n!=null)if(typeof n=="function")l(n,t);else if(typeof n=="object")Array.isArray(n)?s(n):o(n);else throw new TypeError("Expected usable value, not `"+n+"`");return this;function a(u){if(typeof u=="function")l(u,[]);else if(typeof u=="object")if(Array.isArray(u)){const[c,...h]=u;l(c,h)}else o(u);else throw new TypeError("Expected usable value, not `"+u+"`")}function o(u){if(!("plugins"in u)&&!("settings"in u))throw new Error("Expected usable value but received an empty preset, which is probably a mistake: presets typically come with `plugins` and sometimes with `settings`, but this has neither");s(u.plugins),u.settings&&(r.settings=Cn(!0,r.settings,u.settings))}function s(u){let c=-1;if(u!=null)if(Array.isArray(u))for(;++c<u.length;){const h=u[c];a(h)}else throw new TypeError("Expected a list of plugins, not `"+u+"`")}function l(u,c){let h=-1,p=-1;for(;++h<i.length;)if(i[h][0]===u){p=h;break}if(p===-1)i.push([u,...c]);else if(c.length>0){let[d,...f]=c;const w=i[p][1];Qn(w)&&Qn(d)&&(d=Cn(!0,w,d)),i[p]=[u,d,...f]}}}}const al=new dt().freeze();function Tn(e,n){if(typeof n!="function")throw new TypeError("Cannot `"+e+"` without `parser`")}function In(e,n){if(typeof n!="function")throw new TypeError("Cannot `"+e+"` without `compiler`")}function Bn(e,n){if(n)throw new Error("Cannot call `"+e+"` on a frozen processor.\nCreate a new processor first, by calling it: use `processor()` instead of `processor`.")}function ci(e){if(!Qn(e)||typeof e.type!="string")throw new TypeError("Expected node, got `"+e+"`")}function hi(e,n,t){if(!t)throw new Error("`"+e+"` finished async. Use `"+n+"` instead")}function Ze(e){return sl(e)?e:new cr(e)}function sl(e){return!!(e&&typeof e=="object"&&"message"in e&&"messages"in e)}function ll(e){return typeof e=="string"||ul(e)}function ul(e){return!!(e&&typeof e=="object"&&"byteLength"in e&&"byteOffset"in e)}const cl="https://github.com/remarkjs/react-markdown/blob/main/changelog.md",di=[],pi={allowDangerousHtml:!0},hl=/^(https?|ircs?|mailto|xmpp)$/i,dl=[{from:"astPlugins",id:"remove-buggy-html-in-markdown-parser"},{from:"allowDangerousHtml",id:"remove-buggy-html-in-markdown-parser"},{from:"allowNode",id:"replace-allownode-allowedtypes-and-disallowedtypes",to:"allowElement"},{from:"allowedTypes",id:"replace-allownode-allowedtypes-and-disallowedtypes",to:"allowedElements"},{from:"disallowedTypes",id:"replace-allownode-allowedtypes-and-disallowedtypes",to:"disallowedElements"},{from:"escapeHtml",id:"remove-buggy-html-in-markdown-parser"},{from:"includeElementIndex",id:"#remove-includeelementindex"},{from:"includeNodeIndex",id:"change-includenodeindex-to-includeelementindex"},{from:"linkTarget",id:"remove-linktarget"},{from:"plugins",id:"change-plugins-to-remarkplugins",to:"remarkPlugins"},{from:"rawSourcePos",id:"#remove-rawsourcepos"},{from:"renderers",id:"change-renderers-to-components",to:"components"},{from:"source",id:"change-source-to-children",to:"children"},{from:"sourcePos",id:"#remove-sourcepos"},{from:"transformImageUri",id:"#add-urltransform",to:"urlTransform"},{from:"transformLinkUri",id:"#add-urltransform",to:"urlTransform"}];function pl(e){const n=e.allowedElements,t=e.allowElement,i=e.children||"",r=e.className,a=e.components,o=e.disallowedElements,s=e.rehypePlugins||di,l=e.remarkPlugins||di,u=e.remarkRehypeOptions?{...e.remarkRehypeOptions,...pi}:pi,c=e.skipHtml,h=e.unwrapDisallowed,p=e.urlTransform||fl,d=al().use(Ga).use(l).use(Us,u).use(s),f=new cr;typeof i=="string"&&(f.value=i);for(const _ of dl)Object.hasOwn(e,_.from)&&(""+_.from+(_.to?"use `"+_.to+"` instead":"remove it")+cl+_.id,void 0);const w=d.parse(f);let D=d.runSync(w,f);return r&&(D={type:"element",tagName:"div",properties:{className:r},children:D.type==="root"?D.children:[D]}),yn(D,y),q0(D,{Fragment:L.Fragment,components:a,ignoreInvalidStyle:!0,jsx:L.jsx,jsxs:L.jsxs,passKeys:!0,passNode:!0});function y(_,x,E){if(_.type==="raw"&&E&&typeof x=="number")return c?E.children.splice(x,1):E.children[x]={type:"text",value:_.value},x;if(_.type==="element"){let S;for(S in xn)if(Object.hasOwn(xn,S)&&Object.hasOwn(_.properties,S)){const v=_.properties[S],B=xn[S];(B===null||B.includes(_.tagName))&&(_.properties[S]=p(String(v||""),S,_))}}if(_.type==="element"){let S=n?!n.includes(_.tagName):o?o.includes(_.tagName):!1;if(!S&&t&&typeof x=="number"&&(S=!t(_,x,E)),S&&E&&typeof x=="number")return h&&_.children?E.children.splice(x,1,..._.children):E.children.splice(x,1),x}}}function fl(e){const n=e.indexOf(":"),t=e.indexOf("?"),i=e.indexOf("#"),r=e.indexOf("/");return n<0||r>-1&&n>r||t>-1&&n>t||i>-1&&n>i||hl.test(e.slice(0,n))?e:""}function fi(e,n){const t=String(e);if(typeof n!="string")throw new TypeError("Expected character");let i=0,r=t.indexOf(n);for(;r!==-1;)i++,r=t.indexOf(n,r+n.length);return i}function ml(e){if(typeof e!="string")throw new TypeError("Expected a string");return e.replace(/[|\\{}()[\]^$+*?.]/g,"\\$&").replace(/-/g,"\\x2d")}function gl(e,n,t){const r=mn((t||{}).ignore||[]),a=yl(n);let o=-1;for(;++o<a.length;)Kn(e,s);function s(u,c,h){if(u.type==="text"&&typeof h=="number")return l(u,c,h);if(r(u,h,c[c.length-1]))return $n}function l(u,c,h){const p=c[c.length-1],d=a[o][0],f=a[o][1];let w=0,D=!1,y=[];d.lastIndex=0;let _=d.exec(u.value);for(;_;){const E=_.index,S={index:_.index,input:_.input,stack:[...c,u]};let v=f(..._,S);if(typeof v=="string"&&(v=v.length>0?{type:"text",value:v}:void 0),v===!1)d.lastIndex=E+1;else{if(w!==E&&x({type:"text",value:u.value.slice(w,E)}),Array.isArray(v))for(const B of v)x(B);else v&&x(v);w=E+_[0].length,D=!0}if(!d.global)break;_=d.exec(u.value)}return D?(w<u.value.length&&x({type:"text",value:u.value.slice(w)}),p.children.splice(h,1,...y)):y=[u],h+y.length;function x(E){const S=y[y.length-1];S&&S.type==="text"&&E.type==="text"?S.value+=E.value:y.push(E)}}}function yl(e){if(!Array.isArray(e))throw new TypeError("Expected find and replace tuple or list of tuples");const n=[],t=!e[0]||Array.isArray(e[0])?e:[e];let i=-1;for(;++i<t.length;){const r=t[i];n.push([wl(r[0]),bl(r[1])])}return n}function wl(e){return typeof e=="string"?new RegExp(ml(e),"g"):e}function bl(e){return typeof e=="function"?e:function(){return e}}const qn="phrasing",Rn=["autolink","link","image","label"];function kl(){return{transforms:[Fl],enter:{literalAutolink:Dl,literalAutolinkEmail:Pn,literalAutolinkHttp:Pn,literalAutolinkWww:Pn},exit:{literalAutolink:Cl,literalAutolinkEmail:Al,literalAutolinkHttp:xl,literalAutolinkWww:_l}}}function vl(){return{unsafe:[{character:"@",before:"[+\\-.\\w]",after:"[\\-.\\w]",inConstruct:qn,notInConstruct:Rn},{character:".",before:"[Ww]",after:"[\\-.\\w]",inConstruct:qn,notInConstruct:Rn},{character:":",before:"[ps]",after:"\\/",inConstruct:qn,notInConstruct:Rn}]}}function Dl(e){this.enter({type:"link",title:null,url:"",children:[]},e)}function Pn(e){this.config.enter.autolinkProtocol.call(this,e)}function xl(e){this.config.exit.autolinkProtocol.call(this,e)}function _l(e){this.config.exit.data.call(this,e);const n=this.stack[this.stack.length-1];n.type,n.url="http://"+this.sliceSerialize(e)}function Al(e){this.config.exit.autolinkEmail.call(this,e)}function Cl(e){this.exit(e)}function Fl(e){gl(e,[[/(https?:\/\/|www(?=\.))([-.\w]+)([^ \t\r\n]*)/gi,El],[new RegExp("(?<=^|\\s|\\p{P}|\\p{S})([-.\\w+]+)@([-\\w]+(?:\\.[-\\w]+)+)","gu"),Sl]],{ignore:["link","linkReference"]})}function El(e,n,t,i,r){let a="";if(!hr(r)||(/^w/i.test(n)&&(t=n+t,n="",a="http://"),!Tl(t)))return!1;const o=Il(t+i);if(!o[0])return!1;const s={type:"link",title:null,url:a+n+o[0],children:[{type:"text",value:n+o[0]}]};return o[1]?[s,{type:"text",value:o[1]}]:s}function Sl(e,n,t,i){return!hr(i,!0)||/[-\d_]$/.test(t)?!1:{type:"link",title:null,url:"mailto:"+n+"@"+t,children:[{type:"text",value:n+"@"+t}]}}function Tl(e){const n=e.split(".");return!(n.length<2||n[n.length-1]&&(/_/.test(n[n.length-1])||!/[a-zA-Z\d]/.test(n[n.length-1]))||n[n.length-2]&&(/_/.test(n[n.length-2])||!/[a-zA-Z\d]/.test(n[n.length-2])))}function Il(e){const n=/[!"&'),.:;<>?\]}]+$/.exec(e);if(!n)return[e,void 0];e=e.slice(0,n.index);let t=n[0],i=t.indexOf(")");const r=fi(e,"(");let a=fi(e,")");for(;i!==-1&&r>a;)e+=t.slice(0,i+1),t=t.slice(i+1),i=t.indexOf(")"),a++;return[e,t]}function hr(e,n){const t=e.input.charCodeAt(e.index-1);return(e.index===0||Ce(t)||dn(t))&&(!n||t!==47)}dr.peek=Nl;function Bl(){this.buffer()}function ql(e){this.enter({type:"footnoteReference",identifier:"",label:""},e)}function Rl(){this.buffer()}function Pl(e){this.enter({type:"footnoteDefinition",identifier:"",label:"",children:[]},e)}function zl(e){const n=this.resume(),t=this.stack[this.stack.length-1];t.type,t.identifier=he(this.sliceSerialize(e)).toLowerCase(),t.label=n}function Ll(e){this.exit(e)}function Ol(e){const n=this.resume(),t=this.stack[this.stack.length-1];t.type,t.identifier=he(this.sliceSerialize(e)).toLowerCase(),t.label=n}function Ml(e){this.exit(e)}function Nl(){return"["}function dr(e,n,t,i){const r=t.createTracker(i);let a=r.move("[^");const o=t.enter("footnoteReference"),s=t.enter("reference");return a+=r.move(t.safe(t.associationId(e),{after:"]",before:a})),s(),o(),a+=r.move("]"),a}function Hl(){return{enter:{gfmFootnoteCallString:Bl,gfmFootnoteCall:ql,gfmFootnoteDefinitionLabelString:Rl,gfmFootnoteDefinition:Pl},exit:{gfmFootnoteCallString:zl,gfmFootnoteCall:Ll,gfmFootnoteDefinitionLabelString:Ol,gfmFootnoteDefinition:Ml}}}function jl(e){let n=!1;return e&&e.firstLineBlank&&(n=!0),{handlers:{footnoteDefinition:t,footnoteReference:dr},unsafe:[{character:"[",inConstruct:["label","phrasing","reference"]}]};function t(i,r,a,o){const s=a.createTracker(o);let l=s.move("[^");const u=a.enter("footnoteDefinition"),c=a.enter("label");return l+=s.move(a.safe(a.associationId(i),{before:l,after:"]"})),c(),l+=s.move("]:"),i.children&&i.children.length>0&&(s.shift(4),l+=s.move((n?`
`:" ")+a.indentLines(a.containerFlow(i,s.current()),n?pr:Ul))),u(),l}}function Ul(e,n,t){return n===0?e:pr(e,n,t)}function pr(e,n,t){return(t?"":"    ")+e}const Vl=["autolink","destinationLiteral","destinationRaw","reference","titleQuote","titleApostrophe"];pt.attention=Yl;pt.peek=Ql;function Wl(){return{canContainEols:["delete"],enter:{strikethrough:Kl},exit:{strikethrough:Gl}}}function $l(){return{handlers:{delete:pt},unsafe:[{character:"~",inConstruct:"phrasing",notInConstruct:Vl}]}}function Kl(e){this.enter({type:"delete",children:[],position:void 0},e)}function Gl(e){this.exit(e)}function pt(e,n,t,i){const r=t.createTracker(i),a=t.stack.includes("strikethrough")?"~":"~~",o=t.enter("strikethrough");let s=r.move(a);return s+=t.containerPhrasing(e,{...r.current(),before:s,after:"~"}),s+=r.move(a),o(),s}function Yl(){return{construct:"strikethrough",markers:["~"],sizes:[2,1]}}function Ql(){return"~"}function Xl(e){return e.length}function Jl(e,n){const t=n||{},i=(t.align||[]).concat(),r=t.stringLength||Xl,a=[],o=[],s=[],l=[];let u=0,c=-1;for(;++c<e.length;){const w=[],D=[];let y=-1;for(e[c].length>u&&(u=e[c].length);++y<e[c].length;){const _=Zl(e[c][y]);if(t.alignDelimiters!==!1){const x=r(_);D[y]=x,(l[y]===void 0||x>l[y])&&(l[y]=x)}w.push(_)}o[c]=w,s[c]=D}let h=-1;if(typeof i=="object"&&"length"in i)for(;++h<u;)a[h]=mi(i[h]);else{const w=mi(i);for(;++h<u;)a[h]=w}h=-1;const p=[],d=[];for(;++h<u;){const w=a[h];let D="",y="";w===99?(D=":",y=":"):w===108?D=":":w===114&&(y=":");let _=t.alignDelimiters===!1?1:Math.max(1,l[h]-D.length-y.length);const x=D+"-".repeat(_)+y;t.alignDelimiters!==!1&&(_=D.length+_+y.length,_>l[h]&&(l[h]=_),d[h]=_),p[h]=x}o.splice(1,0,p),s.splice(1,0,d),c=-1;const f=[];for(;++c<o.length;){const w=o[c],D=s[c];h=-1;const y=[];for(;++h<u;){const _=w[h]||"";let x="",E="";if(t.alignDelimiters!==!1){const S=l[h]-(D[h]||0),v=a[h];v===114?x=" ".repeat(S):v===99?S%2?(x=" ".repeat(S/2+.5),E=" ".repeat(S/2-.5)):(x=" ".repeat(S/2),E=x):E=" ".repeat(S)}t.delimiterStart!==!1&&!h&&y.push("|"),t.padding!==!1&&!(t.alignDelimiters===!1&&_==="")&&(t.delimiterStart!==!1||h)&&y.push(" "),t.alignDelimiters!==!1&&y.push(x),y.push(_),t.alignDelimiters!==!1&&y.push(E),t.padding!==!1&&y.push(" "),(t.delimiterEnd!==!1||h!==u-1)&&y.push("|")}f.push(t.delimiterEnd===!1?y.join("").replace(/ +$/,""):y.join(""))}return f.join(`
`)}function Zl(e){return e==null?"":String(e)}function mi(e){const n=typeof e=="string"?e.codePointAt(0):0;return n===67||n===99?99:n===76||n===108?108:n===82||n===114?114:0}const e1=mn(["break","delete","emphasis","footnote","footnoteReference","image","imageReference","inlineCode","inlineMath","link","linkReference","mdxJsxTextElement","mdxTextExpression","strong","text","textDirective"]);function n1(e,n,t,i){const r=t.enter("blockquote"),a=t.createTracker(i);a.move("> "),a.shift(2);const o=t.indentLines(t.containerFlow(e,a.current()),t1);return r(),o}function t1(e,n,t){return">"+(t?"":" ")+e}function i1(e,n){return gi(e,n.inConstruct,!0)&&!gi(e,n.notInConstruct,!1)}function gi(e,n,t){if(typeof n=="string"&&(n=[n]),!n||n.length===0)return t;let i=-1;for(;++i<n.length;)if(e.includes(n[i]))return!0;return!1}function yi(e,n,t,i){let r=-1;for(;++r<t.unsafe.length;){const a=t.unsafe[r];if(a.character===`
`&&!a.before&&!a.after&&i1(t.stack,a))return/[\t ]/.test(i.before)?"":" "}return`\\
`}function r1(e,n){const t=String(e);let i=t.indexOf(n),r=i,a=0,o=0;if(typeof n!="string")throw new TypeError("Expected substring");for(;i!==-1;)i===r?++a>o&&(o=a):a=1,r=i+n.length,i=t.indexOf(n,r);return o}function o1(e,n){return!!(n.options.fences===!1&&e.value&&!e.lang&&/[^\n\r ]/.test(e.value)&&!/^[\t ]*(?:[\n\r]|$)|(?:^|[\n\r])[\t ]*$/.test(e.value))}function a1(e){const n=e.options.fence||"`";if(n!=="`"&&n!=="~")throw new Error("Cannot serialize code with `"+n+"` for `options.fence`, expected `` ` `` or `~`");return n}function s1(e,n,t,i){const r=a1(t),a=e.value||"";if(o1(e,t)){const h=t.enter("codeIndented"),p=t.indentLines(a,l1);return h(),p}const o=t.createTracker(i),s=r.repeat(Math.max(r1(a,r)+1,3)),l=t.enter("codeFenced"),u=r==="`"?"GraveAccent":"Tilde";let c=o.move(s);if(e.lang){const h=t.enter(`codeFencedLang${u}`);c+=o.move(t.safe(e.lang,{before:c,after:" ",encode:["`"],...o.current()})),h()}if(e.lang&&e.meta){const h=t.enter(`codeFencedMeta${u}`);c+=o.move(" "),c+=o.move(t.safe(e.meta,{before:c,after:`
`,encode:["`"],...o.current()})),h()}return c+=o.move(`
`),a&&(c+=o.move(a+`
`)),c+=o.move(s),l(),c}function l1(e,n,t){return(t?"":"    ")+e}function ft(e){const n=e.options.quote||'"';if(n!=='"'&&n!=="'")throw new Error("Cannot serialize title with `"+n+"` for `options.quote`, expected `\"`, or `'`");return n}function u1(e,n,t,i){const r=ft(t),a=r==='"'?"Quote":"Apostrophe",o=t.enter("definition");let s=t.enter("label");const l=t.createTracker(i);let u=l.move("[");return u+=l.move(t.safe(t.associationId(e),{before:u,after:"]",...l.current()})),u+=l.move("]: "),s(),!e.url||/[\0- \u007F]/.test(e.url)?(s=t.enter("destinationLiteral"),u+=l.move("<"),u+=l.move(t.safe(e.url,{before:u,after:">",...l.current()})),u+=l.move(">")):(s=t.enter("destinationRaw"),u+=l.move(t.safe(e.url,{before:u,after:e.title?" ":`
`,...l.current()}))),s(),e.title&&(s=t.enter(`title${a}`),u+=l.move(" "+r),u+=l.move(t.safe(e.title,{before:u,after:r,...l.current()})),u+=l.move(r),s()),o(),u}function c1(e){const n=e.options.emphasis||"*";if(n!=="*"&&n!=="_")throw new Error("Cannot serialize emphasis with `"+n+"` for `options.emphasis`, expected `*`, or `_`");return n}function hn(e){const n=e.codePointAt(0);return n===void 0?"":String.fromCodePoint(n)}function qe(e){const n=e.codePointAt(e.length-2);return n!==void 0&&n>65535?e.slice(-2):e.slice(-1)}function fr(e){return"&#x"+e.toString(16).toUpperCase()+";"}function wi(e,n,t){const i=ve(e),r=ve(n);return i===void 0?r===void 0?t==="_"?{inside:!0,outside:!0}:{inside:!1,outside:!1}:r===1?{inside:!0,outside:!0}:{inside:!1,outside:!0}:i===1?r===void 0?{inside:!1,outside:!1}:r===1?{inside:!0,outside:!0}:{inside:!1,outside:!1}:r===void 0?{inside:!1,outside:!1}:r===1?{inside:!0,outside:!1}:{inside:!1,outside:!1}}function h1(e){if(e.charCodeAt(0)!==60)return;const n=e.charCodeAt(1);if(n===33){const s=e.charCodeAt(2);return s===45?2:s===91?5:Q(s)?4:void 0}if(n===63)return 3;const t=n===47,i=t?2:1;let r=i,a=e.charCodeAt(r);if(!Q(a))return;for(;a===45||X(a);)a=e.charCodeAt(++r);const o=e.slice(i,r).toLowerCase();return!t&&a!==47&&Wn.includes(o)?1:Xi.includes(o)?6:7}const d1=new Map([["*",!1],["_",!0]]);function p1(e,n,t){const i=new Set;for(const a of e){const o=t.get(a);if(o&&a.attention&&n.some(s=>s.attention===a.attention))for(const s of o.tokens)i.add(s.attention)}const r=[];for(const a of e)a.attention&&i.delete(a.attention)&&r.push(a.attention);return r.reverse(),r}function mr(e,n,t){const i=[],r=new Map,a=new Map;let o=0;for(;o<e.length;){if(!e[o].attention){o++;continue}const s=e[o].value.charAt(0),l=d1.get(s);let u=o+1;for(;u<e.length&&e[u].attention&&e[u].value.charAt(0)===s;)u++;const c=o?e[o-1].value:n,h=ve(c.charCodeAt(c.length-1)),p=ve((u<e.length?e[u].value:t).charCodeAt(0)),d=!p||p===2&&!!h,f=!h||h===2&&!!p,w={tokens:e.slice(o,u),markers:[],start:0,end:0,open:l?d&&(!!h||!f):d,close:l?f&&(!!p||!d):f,split:l!==void 0};for(const D of w.tokens){r.set(D,[...w.tokens]),a.set(D,w);let y=D.value.length;for(;y--;)w.markers.push(D)}w.end=w.markers.length,i.push(w),o=u}for(m1(i,r),o=-1;++o<e.length;){const s=r.get(e[o]);if(s)return{attention:p1(e,s,a),index:o}}}function en(e,n){const t=e[n?0:e.length-1];if(!t||t.attention)return;const i=n?hn(t.value):qe(t.value),r=fr(i.codePointAt(0));if(n)t.value=r+t.value.slice(i.length);else{let a=t.value.slice(0,t.value.length-i.length),o=0;for(;a.charCodeAt(a.length-1-o)===92;)o++;o%2&&(a+="\\"),t.value=a+r}}function f1(e,n,t,i,r){for(const a of t.attention){const o=n.get(a)||a.sequences[0];for(const s of a.sequences){if(s===o)continue;const l=new Map(n);l.set(a,s);const u=gt(e,l,i,r),c=mr(u,i,r);if(!c||c.index>t.index)return{chosen:l,mistake:c,tokens:u}}}}function m1(e,n){const t=new Map;for(const i of e){const r=i.tokens[0].value.charAt(0);let a=t.get(r);a||(a=[],t.set(r,a));let o=i.close?a.length:0;for(;o--&&i.start<i.end;){const s=a[o],l=s.end-s.start,u=i.end-i.start;if(i.split?(s.close||i.open)&&u%3&&!((l+u)%3):l!==s.markers.length||l!==u)continue;const c=i.split?l>1&&u>1?2:1:u,h=s.markers.slice(s.end-c,s.end),p=i.markers.slice(i.start,i.start+c),d=h[0],f=p[0];if(d===h[c-1]&&d.value.length===c&&f===p[c-1]&&f.value.length===c&&d.attention===f.attention)n.delete(d),n.delete(f);else{const w=[...new Set([...h,...p])];for(const D of w){const y=n.get(D);y&&y.push(...w)}}s.end-=c,i.start+=c,s.start===s.end&&a.splice(o,1),o=a.length}i.open&&i.start<i.end&&a.push(i)}}function g1(e,n,t){if(n.length===0)throw new Error("Cannot serialize `"+e+"` as attention without markers, expected one or more markers");if(t.length===0)throw new Error("Cannot serialize `"+e+"` as attention without sizes, expected one or more sizes");for(const r of t)if(!Number.isSafeInteger(r)||r<1)throw new Error("Cannot serialize `"+e+"` as attention with `"+r+"` as size, expected positive integer");const i=[];for(const r of n){if(r.length!==1)throw new Error("Cannot serialize `"+e+"` as attention with `"+r+"` as marker, expected a single ascii character");if(!ji(r.charCodeAt(0)))throw new Error("Cannot serialize `"+e+"` as attention with `"+r+"` as marker, expected ascii punctuation");for(const a of t)i.push(r.repeat(a))}return i}function y1(e,n,t){const i=n.indexStack,r=e.children||[],a=[];let o=-1,s=t.before;i.push(-1);let l=n.createTracker(t);for(;++o<r.length;){const u=r[o];let c;if(i[i.length-1]=o,o+1<r.length){let d=n.handle.handlers[r[o+1].type];d&&d.peek&&(d=d.peek),c=d?hn(d(r[o+1],e,n,{before:"",after:"",...l.current()})):""}else c=t.after;const h=a[a.length-1];typeof h=="string"&&(s==="\r"||s===`
`)&&u.type==="html"&&h1(u.value)!==7&&(a[a.length-1]=h.replace(/(\r?\n|\r)$/," "),s=" ",l=n.createTracker(t),l.move(wn(a,t.before,t.after)));const p=n.handle.handlers[u.type];if(p&&p.attention){const d=mt(u,p.attention,n,l);a.push(d),s=qe(d.sequences[0])}else{const d=n.handle(u,e,n,{...l.current(),after:c,before:s});if(!d)continue;l.move(d),a.push(d),s=qe(d)}}return i.pop(),a}function mt(e,n,t,i){const{construct:r,markers:a,sizes:o}=n(e,t),s=g1(e.type,a,o),l=s[0],u=t.enter(r);i.move(l);const c=y1(e,t,{...i.current(),before:l,after:l});return i.move(wn(c,l,l)),i.move(l),u(),{children:c,sequences:s}}function gt(e,n,t,i){const r=[];let a,o=qe(t),s=-1;for(;++s<e.length;){const l=e[s];if(typeof l=="string"){const x={value:l,attention:void 0};a&&a===hn(l)&&en([x],!0),a=void 0,r.push(x),x.value&&(o=qe(x.value));continue}const u=n.get(l)||l.sequences[0],c=u.charAt(0),h=e[s+1],p=o,d=hn(h===void 0?i:typeof h=="string"?h:n.get(h)||h.sequences[0]),f=gt(l.children,n,u,u),w=f.length>0?f[0].value:"",D=wi(p.charCodeAt(p.length-1),w.charCodeAt(0),c);D.inside&&en(f,!0);const y=f.length>0?qe(f[f.length-1].value):"",_=wi(d.charCodeAt(0),y.charCodeAt(y.length-1),c);_.inside&&en(f,!1),D.outside&&p!==`
`&&p!=="\r"&&en(r,!1),_.outside&&(a=d),r.push({value:u,attention:l},...f,{value:u,attention:l}),o=u.charAt(u.length-1)}return r}function wn(e,n,t){let i=new Map;const r=gt(e,i,n,t);let a=r,o=mr(a,n,t);for(;o;){const l=f1(e,i,o,n,t);if(!l){a=r;break}i=l.chosen,a=l.tokens,o=l.mistake}let s="";for(const l of a)s+=l.value;return s}yt.attention=gr;yt.peek=w1;function yt(e,n,t,i){const r=t.enter("phrasing"),a=mt(e,gr,t,t.createTracker(i)),o=wn([a],i.before,i.after);return r(),o}function gr(e,n){return{construct:"emphasis",markers:c1(n)==="*"?["*","_"]:["_","*"],sizes:[1]}}function w1(e,n,t){return t.options.emphasis||"*"}function b1(e,n){let t=!1;return yn(e,function(i){if("value"in i&&/\r?\n|\r/.test(i.value)||i.type==="break")return t=!0,on}),!!((!e.depth||e.depth<3)&&ot(e)&&(n.options.setext||t))}function k1(e,n,t,i){const r=Math.max(Math.min(6,e.depth||1),1),a=t.createTracker(i);if(b1(e,t)){const h=t.enter("headingSetext"),p=t.enter("phrasing"),d=t.containerPhrasing(e,{...a.current(),before:`
`,after:`
`});return p(),h(),d+`
`+(r===1?"=":"-").repeat(d.length-(Math.max(d.lastIndexOf("\r"),d.lastIndexOf(`
`))+1))}const o="#".repeat(r),s=t.enter("headingAtx"),l=t.enter("phrasing");a.move(o+" ");let u=t.containerPhrasing(e,{before:"# ",after:`
`,...a.current()});const c=u.charCodeAt(0);return(c===9||c===32)&&(u=fr(c)+u.slice(1)),u=u?o+" "+u:o,t.options.closeAtx&&(u+=" "+o),l(),s(),u}yr.peek=v1;function yr(e){return e.value||""}function v1(){return"<"}wr.peek=D1;function wr(e,n,t,i){const r=ft(t),a=r==='"'?"Quote":"Apostrophe",o=t.enter("image");let s=t.enter("label");const l=t.createTracker(i);let u=l.move("![");return u+=l.move(t.safe(e.alt,{before:u,after:"]",...l.current()})),u+=l.move("]("),s(),!e.url&&e.title||/[\0- \u007F]/.test(e.url)?(s=t.enter("destinationLiteral"),u+=l.move("<"),u+=l.move(t.safe(e.url,{before:u,after:">",...l.current()})),u+=l.move(">")):(s=t.enter("destinationRaw"),u+=l.move(t.safe(e.url,{before:u,after:e.title?" ":")",...l.current()}))),s(),e.title&&(s=t.enter(`title${a}`),u+=l.move(" "+r),u+=l.move(t.safe(e.title,{before:u,after:r,...l.current()})),u+=l.move(r),s()),u+=l.move(")"),o(),u}function D1(){return"!"}br.peek=x1;function br(e,n,t,i){const r=e.referenceType,a=t.enter("imageReference");let o=t.enter("label");const s=t.createTracker(i);let l=s.move("![");const u=t.safe(e.alt,{before:l,after:"]",...s.current()});l+=s.move(u+"]["),o();const c=t.stack;t.stack=c.filter(function(p){return p!=="phrasing"}),o=t.enter("reference");const h=t.safe(t.associationId(e),{before:l,after:"]",...s.current()});return o(),t.stack=c,a(),r==="full"||!u||u!==h?l+=s.move(h+"]"):r==="shortcut"?l=l.slice(0,-1):l+=s.move("]"),l}function x1(){return"!"}kr.peek=_1;function kr(e,n,t){let i=e.value||"",r="`",a=-1;for(;new RegExp("(^|[^`])"+r+"([^`]|$)").test(i);)r+="`";for(/[^\n\r ]/.test(i)&&(/^[\n\r ]/.test(i)&&/[\n\r ]$/.test(i)||/^`|`$/.test(i))&&(i=" "+i+" ");++a<t.unsafe.length;){const o=t.unsafe[a],s=t.compilePattern(o);if(!o.atBreak)continue;let l;for(;l=s.exec(i);){let u=l.index;i.charCodeAt(u)===10&&i.charCodeAt(u-1)===13&&u--,i=i.slice(0,u)+" "+i.slice(l.index+1)}}return r+i+r}function _1(){return"`"}function vr(e,n){const t=ot(e);return!!(!n.options.resourceLink&&e.url&&!e.title&&e.children&&e.children.length===1&&e.children[0].type==="text"&&(t===e.url||"mailto:"+t===e.url)&&/^[a-z][+\-.a-z]+:/i.test(e.url)&&!/[\0- <>\u007F]/.test(e.url))}Dr.peek=A1;function Dr(e,n,t,i){const r=ft(t),a=r==='"'?"Quote":"Apostrophe",o=t.createTracker(i);if(vr(e,t)){const f=t.stack;t.stack=f.filter(function(y){return y!=="phrasing"});const w=t.enter("autolink");let D=o.move("<");return D+=o.move(t.containerPhrasing(e,{before:D,after:">",...o.current()})),D+=o.move(">"),w(),t.stack=f,D}const s=t.enter("link");let l=t.enter("label"),u=o.move("[");const c=t.containerPhrasing(e,{before:u,after:"](",...o.current()});u+=o.move(c),l(),u+=o.move("](");const h=/[\0- \u007F]/.test(e.url),p=i.before.charAt(i.before.length-1);let d=e.title||void 0;if(!d&&!h&&(p===`
`||p==="\r")){let f=0;for(;f<c.length&&c.charCodeAt(f)!==93;)f+=c.charCodeAt(f)===92?2:1;c.charCodeAt(f+1)===58&&(d="")}return!e.url&&typeof d=="string"||h?(l=t.enter("destinationLiteral"),u+=o.move("<"),u+=o.move(t.safe(e.url,{before:u,after:">",...o.current()})),u+=o.move(">")):(l=t.enter("destinationRaw"),u+=o.move(t.safe(e.url,{before:u,after:typeof d=="string"?" ":")",...o.current()}))),l(),typeof d=="string"&&(l=t.enter(`title${a}`),u+=o.move(" "+r),u+=o.move(t.safe(d,{before:u,after:r,...o.current()})),u+=o.move(r),l()),u+=o.move(")"),s(),u}function A1(e,n,t){return vr(e,t)?"<":"["}xr.peek=C1;function xr(e,n,t,i){const r=e.referenceType,a=t.enter("linkReference");let o=t.enter("label");const s=t.createTracker(i);let l=s.move("[");const u=t.containerPhrasing(e,{before:l,after:"]",...s.current()});l+=s.move(u+"]["),o();const c=t.stack;t.stack=c.filter(function(p){return p!=="phrasing"}),o=t.enter("reference");const h=t.safe(t.associationId(e),{before:l,after:"]",...s.current()});return o(),t.stack=c,a(),r==="full"||!u||u!==h?l+=s.move(h+"]"):r==="shortcut"?l=l.slice(0,-1):l+=s.move("]"),l}function C1(){return"["}function wt(e){const n=e.options.bullet||"*";if(n!=="*"&&n!=="+"&&n!=="-")throw new Error("Cannot serialize items with `"+n+"` for `options.bullet`, expected `*`, `+`, or `-`");return n}function F1(e){const n=wt(e),t=e.options.bulletOther;if(!t)return n==="*"?"-":"*";if(t!=="*"&&t!=="+"&&t!=="-")throw new Error("Cannot serialize items with `"+t+"` for `options.bulletOther`, expected `*`, `+`, or `-`");if(t===n)throw new Error("Expected `bullet` (`"+n+"`) and `bulletOther` (`"+t+"`) to be different");return t}function E1(e){const n=e.options.bulletOrdered||".";if(n!=="."&&n!==")")throw new Error("Cannot serialize items with `"+n+"` for `options.bulletOrdered`, expected `.` or `)`");return n}function _r(e){const n=e.options.rule||"*";if(n!=="*"&&n!=="-"&&n!=="_")throw new Error("Cannot serialize rules with `"+n+"` for `options.rule`, expected `*`, `-`, or `_`");return n}function S1(e,n,t,i){const r=t.enter("list"),a=t.bulletCurrent;let o=e.ordered?E1(t):wt(t);const s=e.ordered?o==="."?")":".":F1(t);let l=n&&t.bulletLastUsed?o===t.bulletLastUsed:!1;if(!e.ordered){const c=e.children?e.children[0]:void 0;if((o==="*"||o==="-")&&c&&(!c.children||!c.children[0])&&t.stack[t.stack.length-1]==="list"&&t.stack[t.stack.length-2]==="listItem"&&t.stack[t.stack.length-3]==="list"&&t.stack[t.stack.length-4]==="listItem"&&t.indexStack[t.indexStack.length-1]===0&&t.indexStack[t.indexStack.length-2]===0&&t.indexStack[t.indexStack.length-3]===0&&(l=!0),_r(t)===o&&c){let h=-1;for(;++h<e.children.length;){const p=e.children[h];if(p&&p.type==="listItem"&&p.children&&p.children[0]&&p.children[0].type==="thematicBreak"){l=!0;break}}}}l&&(o=s),t.bulletCurrent=o;const u=t.containerFlow(e,i);return t.bulletLastUsed=o,t.bulletCurrent=a,r(),u}function T1(e){const n=e.options.listItemIndent||"one";if(n!=="tab"&&n!=="one"&&n!=="mixed")throw new Error("Cannot serialize items with `"+n+"` for `options.listItemIndent`, expected `tab`, `one`, or `mixed`");return n}function I1(e,n,t,i){const r=T1(t);let a=t.bulletCurrent||wt(t);n&&n.type==="list"&&n.ordered&&(a=(typeof n.start=="number"&&n.start>-1?n.start:1)+(t.options.incrementListMarker===!1?0:n.children.indexOf(e))+a);let o=a.length+1;(r==="tab"||r==="mixed"&&(n&&n.type==="list"&&n.spread||e.spread))&&(o=Math.ceil(o/4)*4);const s=t.createTracker(i);s.move(a+" ".repeat(o-a.length)),s.shift(o);const l=t.enter("listItem"),u=t.indentLines(t.containerFlow(e,s.current()),c);return l(),u;function c(h,p,d){return p?(d?"":" ".repeat(o))+h:(d?a:a+" ".repeat(o-a.length))+h}}function B1(e,n,t,i){const r=t.enter("paragraph"),a=t.enter("phrasing"),o=t.containerPhrasing(e,i);return a(),r(),o}function q1(e,n,t,i){if(!e.children.some(function(s){return e1(s)}))return t.containerFlow(e,i);const a=t.enter("phrasing"),o=t.containerPhrasing(e,i);return a(),o}function R1(e){const n=e.options.strong||"*";if(n!=="*"&&n!=="_")throw new Error("Cannot serialize strong with `"+n+"` for `options.strong`, expected `*`, or `_`");return n}bt.attention=Ar;bt.peek=P1;function bt(e,n,t,i){const r=t.enter("phrasing"),a=mt(e,Ar,t,t.createTracker(i)),o=wn([a],i.before,i.after);return r(),o}function Ar(e,n){return{construct:"strong",markers:R1(n)==="*"?["*","_"]:["_","*"],sizes:[2]}}function P1(e,n,t){return t.options.strong||"*"}function z1(e,n,t,i){const r=n?n.children:[],a=t.indexStack[t.indexStack.length-1];return t.safe(e.value,{...i,afterNode:r[a+1],beforeNode:r[a-1]})}function L1(e){const n=e.options.ruleRepetition||3;if(n<3)throw new Error("Cannot serialize rules with repetition `"+n+"` for `options.ruleRepetition`, expected `3` or more");return n}function O1(e,n,t){const i=(_r(t)+(t.options.ruleSpaces?" ":"")).repeat(L1(t));return t.options.ruleSpaces?i.slice(0,-1):i}const Cr={blockquote:n1,break:yi,code:s1,definition:u1,emphasis:yt,hardBreak:yi,heading:k1,html:yr,image:wr,imageReference:br,inlineCode:kr,link:Dr,linkReference:xr,list:S1,listItem:I1,paragraph:B1,root:q1,strong:bt,text:z1,thematicBreak:O1};function M1(){return{enter:{table:N1,tableData:bi,tableHeader:bi,tableRow:j1},exit:{codeText:U1,table:H1,tableData:zn,tableHeader:zn,tableRow:zn}}}function N1(e){const n=e._align;this.enter({type:"table",align:n.map(function(t){return t==="none"?null:t}),children:[]},e),this.data.inTable=!0}function H1(e){this.exit(e),this.data.inTable=void 0}function j1(e){this.enter({type:"tableRow",children:[]},e)}function zn(e){this.exit(e)}function bi(e){this.enter({type:"tableCell",children:[]},e)}function U1(e){let n=this.resume();this.data.inTable&&(n=n.replace(/\\([\\|])/g,V1));const t=this.stack[this.stack.length-1];t.type,t.value=n,this.exit(e)}function V1(e,n){return n==="|"?n:e}function W1(e){const n=e||{},t=n.tableCellPadding,i=n.tablePipeAlign,r=n.stringLength,a=t?" ":"|";return{unsafe:[{character:"\r",inConstruct:"tableCell"},{character:`
`,inConstruct:"tableCell"},{atBreak:!0,character:"|",after:"[	 :-]"},{character:"|",inConstruct:"tableCell"},{atBreak:!0,character:":",after:"-"},{atBreak:!0,character:"-",after:"[:|-]"}],handlers:{inlineCode:p,table:o,tableCell:l,tableRow:s}};function o(d,f,w,D){return u(c(d,w,D),d.align)}function s(d,f,w,D){const y=h(d,w,D),_=u([y]);return _.slice(0,_.indexOf(`
`))}function l(d,f,w,D){const y=w.enter("tableCell"),_=w.enter("phrasing"),x=w.containerPhrasing(d,{...D,before:a,after:a});return _(),y(),x}function u(d,f){return Jl(d,{align:f,alignDelimiters:i,padding:t,stringLength:r})}function c(d,f,w){const D=d.children;let y=-1;const _=[],x=f.enter("table");for(;++y<D.length;)_[y]=h(D[y],f,w);return x(),_}function h(d,f,w){const D=d.children;let y=-1;const _=[],x=f.enter("tableRow");for(;++y<D.length;)_[y]=l(D[y],d,f,w);return x(),_}function p(d,f,w){let D=Cr.inlineCode(d,f,w);return w.stack.includes("tableCell")&&(D=D.replace(/\|/g,"\\$&")),D}}function $1(){return{exit:{taskListCheckValueChecked:ki,taskListCheckValueUnchecked:ki,paragraph:G1}}}function K1(){return{unsafe:[{atBreak:!0,character:"-",after:"[:|-]"}],handlers:{listItem:Y1}}}function ki(e){const n=this.stack[this.stack.length-2];n.type,n.checked=e.type==="taskListCheckValueChecked"}function G1(e){const n=this.stack[this.stack.length-2];if(n&&n.type==="listItem"&&typeof n.checked=="boolean"){const t=this.stack[this.stack.length-1];t.type;const i=t.children[0];if(i&&i.type==="text"){const r=n.children;let a=-1,o;for(;++a<r.length;){const s=r[a];if(s.type==="paragraph"){o=s;break}}o===t&&(i.value=i.value.slice(1),i.value.length===0?t.children.shift():t.position&&i.position&&typeof i.position.start.offset=="number"&&(i.position.start.column++,i.position.start.offset++,t.position.start=Object.assign({},i.position.start)))}}this.exit(e)}function Y1(e,n,t,i){const r=e.children[0],a=typeof e.checked=="boolean"&&r&&r.type==="paragraph",o="["+(e.checked?"x":" ")+"] ",s=t.createTracker(i);a&&s.move(o);let l=Cr.listItem(e,n,t,{...i,...s.current()});return a&&(l=l.replace(/^(?:[*+-]|\d+\.)([\r\n]| {1,3})/,u)),l;function u(c){return c+o}}function Q1(){return[kl(),Hl(),Wl(),M1(),$1()]}function X1(e){return{extensions:[vl(),jl(e),$l(),W1(e),K1()]}}const J1={tokenize:ru,partial:!0},Fr={tokenize:ou,partial:!0},Er={tokenize:au,partial:!0},Sr={tokenize:su,partial:!0},Z1={tokenize:lu,partial:!0},Tr={name:"wwwAutolink",tokenize:tu,previous:Br},Ir={name:"protocolAutolink",tokenize:iu,previous:qr},we={name:"emailAutolink",tokenize:nu,previous:Rr},fe={};function eu(){return{text:fe}}let xe=48;for(;xe<123;)fe[xe]=we,xe++,xe===58?xe=65:xe===91&&(xe=97);fe[43]=we;fe[45]=we;fe[46]=we;fe[95]=we;fe[72]=[we,Ir];fe[104]=[we,Ir];fe[87]=[we,Tr];fe[119]=[we,Tr];function nu(e,n,t){const i=this;let r,a;return o;function o(h){return!Jn(h)||!Rr.call(i,i.previous)||kt(i.events)?t(h):(e.enter("literalAutolink"),e.enter("literalAutolinkEmail"),s(h))}function s(h){return Jn(h)?(e.consume(h),s):h===64?(e.consume(h),l):t(h)}function l(h){return h===46?e.check(Z1,c,u)(h):h===45||h===95||X(h)?(a=!0,e.consume(h),l):c(h)}function u(h){return e.consume(h),r=!0,l}function c(h){return a&&r&&Q(i.previous)?(e.exit("literalAutolinkEmail"),e.exit("literalAutolink"),n(h)):t(h)}}function tu(e,n,t){const i=this;return r;function r(o){return o!==87&&o!==119||!Br.call(i,i.previous)||kt(i.events)?t(o):(e.enter("literalAutolink"),e.enter("literalAutolinkWww"),e.check(J1,e.attempt(Fr,e.attempt(Er,a),t),t)(o))}function a(o){return e.exit("literalAutolinkWww"),e.exit("literalAutolink"),n(o)}}function iu(e,n,t){const i=this;let r="",a=!1;return o;function o(h){return(h===72||h===104)&&qr.call(i,i.previous)&&!kt(i.events)?(e.enter("literalAutolink"),e.enter("literalAutolinkHttp"),r+=String.fromCodePoint(h),e.consume(h),s):t(h)}function s(h){if(Q(h)&&r.length<5)return r+=String.fromCodePoint(h),e.consume(h),s;if(h===58){const p=r.toLowerCase();if(p==="http"||p==="https")return e.consume(h),l}return t(h)}function l(h){return h===47?(e.consume(h),a?u:(a=!0,l)):t(h)}function u(h){return h===null||sn(h)||U(h)||Ce(h)||dn(h)?t(h):e.attempt(Fr,e.attempt(Er,c),t)(h)}function c(h){return e.exit("literalAutolinkHttp"),e.exit("literalAutolink"),n(h)}}function ru(e,n,t){let i=0;return r;function r(o){return(o===87||o===119)&&i<3?(i++,e.consume(o),r):o===46&&i===3?(e.consume(o),a):t(o)}function a(o){return o===null?t(o):n(o)}}function ou(e,n,t){let i,r,a;return o;function o(u){return u===46||u===95?e.check(Sr,l,s)(u):u===null||U(u)||Ce(u)||u!==45&&dn(u)?l(u):(a=!0,e.consume(u),o)}function s(u){return u===95?i=!0:(r=i,i=void 0),e.consume(u),o}function l(u){return r||i||!a?t(u):n(u)}}function au(e,n){let t=0,i=0;return r;function r(o){return o===40?(t++,e.consume(o),r):o===41&&i<t?a(o):o===33||o===34||o===38||o===39||o===41||o===42||o===44||o===46||o===58||o===59||o===60||o===63||o===93||o===95||o===126?e.check(Sr,n,a)(o):o===null||U(o)||Ce(o)?n(o):(e.consume(o),r)}function a(o){return o===41&&i++,e.consume(o),r}}function su(e,n,t){return i;function i(s){return s===33||s===34||s===39||s===41||s===42||s===44||s===46||s===58||s===59||s===63||s===95||s===126?(e.consume(s),i):s===38?(e.consume(s),a):s===93?(e.consume(s),r):s===60||s===null||U(s)||Ce(s)?n(s):t(s)}function r(s){return s===null||s===40||s===91||U(s)||Ce(s)?n(s):i(s)}function a(s){return Q(s)?o(s):t(s)}function o(s){return s===59?(e.consume(s),i):Q(s)?(e.consume(s),o):t(s)}}function lu(e,n,t){return i;function i(a){return e.consume(a),r}function r(a){return X(a)?t(a):n(a)}}function Br(e){return e===null||e===40||e===42||e===95||e===91||e===93||e===126||U(e)}function qr(e){return!Q(e)}function Rr(e){return!(e===47||Jn(e))}function Jn(e){return e===43||e===45||e===46||e===95||X(e)}function kt(e){let n=e.length,t=!1;for(;n--;){const i=e[n][1];if((i.type==="labelLink"||i.type==="labelImage")&&!i._balanced){t=!0;break}if(i._gfmAutolinkLiteralWalkedInto){t=!1;break}}return e.length>0&&!t&&(e[e.length-1][1]._gfmAutolinkLiteralWalkedInto=!0),t}const uu={tokenize:yu,partial:!0};function cu(){return{document:{91:{name:"gfmFootnoteDefinition",tokenize:fu,continuation:{tokenize:mu},exit:gu}},text:{91:{name:"gfmFootnoteCall",tokenize:pu},93:{name:"gfmPotentialFootnoteCall",add:"after",tokenize:hu,resolveTo:du}}}}function hu(e,n,t){const i=this;let r=i.events.length;const a=i.parser.gfmFootnotes||(i.parser.gfmFootnotes=[]);let o;for(;r--;){const l=i.events[r][1];if(l.type==="labelImage"){o=l;break}if(l.type==="gfmFootnoteCall"||l.type==="labelLink"||l.type==="label"||l.type==="image"||l.type==="link")break}return s;function s(l){if(!o||!o._balanced)return t(l);const u=he(i.sliceSerialize({start:o.end,end:i.now()}));return u.codePointAt(0)!==94||!a.includes(u.slice(1))?t(l):(e.enter("gfmFootnoteCallLabelMarker"),e.consume(l),e.exit("gfmFootnoteCallLabelMarker"),n(l))}}function du(e,n){let t=e.length;for(;t--;)if(e[t][1].type==="labelImage"&&e[t][0]==="enter"){e[t][1];break}e[t+1][1].type="data",e[t+3][1].type="gfmFootnoteCallLabelMarker";const i={type:"gfmFootnoteCall",start:Object.assign({},e[t+3][1].start),end:Object.assign({},e[e.length-1][1].end)},r={type:"gfmFootnoteCallMarker",start:Object.assign({},e[t+3][1].end),end:Object.assign({},e[t+3][1].end)};r.end.column++,r.end.offset++,r.end._bufferIndex++;const a={type:"gfmFootnoteCallString",start:Object.assign({},r.end),end:Object.assign({},e[e.length-1][1].start)},o={type:"chunkString",contentType:"string",start:Object.assign({},a.start),end:Object.assign({},a.end)},s=[e[t+1],e[t+2],["enter",i,n],e[t+3],e[t+4],["enter",r,n],["exit",r,n],["enter",a,n],["enter",o,n],["exit",o,n],["exit",a,n],e[e.length-2],e[e.length-1],["exit",i,n]];return e.splice(t,e.length-t+1,...s),e}function pu(e,n,t){const i=this,r=i.parser.gfmFootnotes||(i.parser.gfmFootnotes=[]);let a=0,o;return s;function s(h){return e.enter("gfmFootnoteCall"),e.enter("gfmFootnoteCallLabelMarker"),e.consume(h),e.exit("gfmFootnoteCallLabelMarker"),l}function l(h){return h!==94?t(h):(e.enter("gfmFootnoteCallMarker"),e.consume(h),e.exit("gfmFootnoteCallMarker"),e.enter("gfmFootnoteCallString"),e.enter("chunkString").contentType="string",u)}function u(h){if(a>999||h===93&&!o||h===null||h===91||U(h))return t(h);if(h===93){e.exit("chunkString");const p=e.exit("gfmFootnoteCallString");return r.includes(he(i.sliceSerialize(p)))?(e.enter("gfmFootnoteCallLabelMarker"),e.consume(h),e.exit("gfmFootnoteCallLabelMarker"),e.exit("gfmFootnoteCall"),n):t(h)}return U(h)||(o=!0),a++,e.consume(h),h===92?c:u}function c(h){return h===91||h===92||h===93?(e.consume(h),a++,u):u(h)}}function fu(e,n,t){const i=this,r=i.parser.gfmFootnotes||(i.parser.gfmFootnotes=[]);let a,o=0,s;return l;function l(f){return e.enter("gfmFootnoteDefinition")._container=!0,e.enter("gfmFootnoteDefinitionLabel"),e.enter("gfmFootnoteDefinitionLabelMarker"),e.consume(f),e.exit("gfmFootnoteDefinitionLabelMarker"),u}function u(f){return f===94?(e.enter("gfmFootnoteDefinitionMarker"),e.consume(f),e.exit("gfmFootnoteDefinitionMarker"),e.enter("gfmFootnoteDefinitionLabelString"),e.enter("chunkString").contentType="string",c):t(f)}function c(f){if(o>999||f===93&&!s||f===null||f===91||U(f))return t(f);if(f===93){e.exit("chunkString");const w=e.exit("gfmFootnoteDefinitionLabelString");return a=he(i.sliceSerialize(w)),e.enter("gfmFootnoteDefinitionLabelMarker"),e.consume(f),e.exit("gfmFootnoteDefinitionLabelMarker"),e.exit("gfmFootnoteDefinitionLabel"),p}return U(f)||(s=!0),o++,e.consume(f),f===92?h:c}function h(f){return f===91||f===92||f===93?(e.consume(f),o++,c):c(f)}function p(f){return f===58?(e.enter("definitionMarker"),e.consume(f),e.exit("definitionMarker"),r.includes(a)||r.push(a),M(e,d,"gfmFootnoteDefinitionWhitespace")):t(f)}function d(f){return n(f)}}function mu(e,n,t){return e.check(Ge,n,e.attempt(uu,n,t))}function gu(e){e.exit("gfmFootnoteDefinition")}function yu(e,n,t){const i=this;return M(e,r,"gfmFootnoteDefinitionIndent",5);function r(a){const o=i.events[i.events.length-1];return o&&o[1].type==="gfmFootnoteDefinitionIndent"&&o[2].sliceSerialize(o[1],!0).length===4?n(a):t(a)}}function wu(e){let t=(e||{}).singleTilde;const i={name:"strikethrough",tokenize:a,resolveAll:r};return t==null&&(t=!0),{text:{126:i},insideSpan:{null:[i]},attentionMarkers:{null:[126]}};function r(o,s){let l=-1;for(;++l<o.length;)if(o[l][0]==="enter"&&o[l][1].type==="strikethroughSequenceTemporary"&&o[l][1]._close){let u=l;for(;u--;)if(o[u][0]==="exit"&&o[u][1].type==="strikethroughSequenceTemporary"&&o[u][1]._open&&o[l][1].end.offset-o[l][1].start.offset===o[u][1].end.offset-o[u][1].start.offset){o[l][1].type="strikethroughSequence",o[u][1].type="strikethroughSequence";const c={type:"strikethrough",start:Object.assign({},o[u][1].start),end:Object.assign({},o[l][1].end)},h={type:"strikethroughText",start:Object.assign({},o[u][1].end),end:Object.assign({},o[l][1].start)},p=[["enter",c,s],["enter",o[u][1],s],["exit",o[u][1],s],["enter",h,s]],d=s.parser.constructs.insideSpan.null;d&&ce(p,p.length,0,pn(d,o.slice(u+1,l),s)),ce(p,p.length,0,[["exit",h,s],["enter",o[l][1],s],["exit",o[l][1],s],["exit",c,s]]),ce(o,u-1,l-u+3,p),l=u+p.length-2;break}}for(l=-1;++l<o.length;)o[l][1].type==="strikethroughSequenceTemporary"&&(o[l][1].type="data");return o}function a(o,s,l){const u=this.previous,c=this.events;let h=0;return p;function p(f){return u===126&&c[c.length-1][1].type!=="characterEscape"?l(f):(o.enter("strikethroughSequenceTemporary"),d(f))}function d(f){const w=ve(u);if(f===126)return h>1?l(f):(o.consume(f),h++,d);if(h<2&&!t)return l(f);const D=o.exit("strikethroughSequenceTemporary"),y=ve(f);return D._open=!y||y===2&&!!w,D._close=!w||w===2&&!!y,s(f)}}}class bu{constructor(){this.map=[],this.index=new Map}add(n,t,i){ku(this,n,t,i)}consume(n){if(this.map.sort(function(a,o){return a[0]-o[0]}),this.map.length===0)return;let t=this.map.length;const i=[];for(;t>0;)t-=1,i.push(n.slice(this.map[t][0]+this.map[t][1]),this.map[t][2]),n.length=this.map[t][0];i.push(n.slice()),n.length=0;let r=i.pop();for(;r;){for(const a of r)n.push(a);r=i.pop()}this.map.length=0,this.index.clear()}}function ku(e,n,t,i){if(t===0&&i.length===0)return;const r=e.index.get(n);if(r){r[1]+=t,r[2].push(...i);return}const a=[n,t,i];e.map.push(a),e.index.set(n,a)}function vu(e,n){let t=!1;const i=[];for(;n<e.length;){const r=e[n];if(t){if(r[0]==="enter")r[1].type==="tableContent"&&i.push(e[n+1][1].type==="tableDelimiterMarker"?"left":"none");else if(r[1].type==="tableContent"){if(e[n-1][1].type==="tableDelimiterMarker"){const a=i.length-1;i[a]=i[a]==="left"?"center":"right"}}else if(r[1].type==="tableDelimiterRow")break}else r[0]==="enter"&&r[1].type==="tableDelimiterRow"&&(t=!0);n+=1}return i}function Du(){return{flow:{null:{name:"table",tokenize:xu,resolveAll:_u}}}}function xu(e,n,t){const i=this;let r=0,a=0,o;return s;function s(b){let F=i.events.length-1;for(;F>-1;){const{type:W}=i.events[F][1];if(W==="lineEnding"||W==="linePrefix")F--;else break}const I=F>-1?i.events[F][1].type:null,H=I==="tableHead"||I==="tableRow"?v:l;return H===v&&i.parser.lazy[i.now().line]?t(b):H(b)}function l(b){return e.enter("tableHead"),e.enter("tableRow"),u(b)}function u(b){return b===124||(o=!0,a+=1),c(b)}function c(b){return b===null?t(b):T(b)?a>1?(a=0,i.interrupt=!0,e.exit("tableRow"),e.enter("lineEnding"),e.consume(b),e.exit("lineEnding"),d):t(b):z(b)?M(e,c,"whitespace")(b):(a+=1,o&&(o=!1,r+=1),b===124?(e.enter("tableCellDivider"),e.consume(b),e.exit("tableCellDivider"),o=!0,c):(e.enter("data"),h(b)))}function h(b){return b===null||b===124||U(b)?(e.exit("data"),c(b)):(e.consume(b),b===92?p:h)}function p(b){return b===92||b===124?(e.consume(b),h):h(b)}function d(b){return i.interrupt=!1,i.parser.lazy[i.now().line]?t(b):(e.enter("tableDelimiterRow"),o=!1,z(b)?M(e,f,"linePrefix",i.parser.constructs.disable.null.includes("codeIndented")?void 0:4)(b):f(b))}function f(b){return b===45||b===58?D(b):b===124?(o=!0,e.enter("tableCellDivider"),e.consume(b),e.exit("tableCellDivider"),w):S(b)}function w(b){return z(b)?M(e,D,"whitespace")(b):D(b)}function D(b){return b===58?(a+=1,o=!0,e.enter("tableDelimiterMarker"),e.consume(b),e.exit("tableDelimiterMarker"),y):b===45?(a+=1,y(b)):b===null||T(b)?E(b):S(b)}function y(b){return b===45?(e.enter("tableDelimiterFiller"),_(b)):S(b)}function _(b){return b===45?(e.consume(b),_):b===58?(o=!0,e.exit("tableDelimiterFiller"),e.enter("tableDelimiterMarker"),e.consume(b),e.exit("tableDelimiterMarker"),x):(e.exit("tableDelimiterFiller"),x(b))}function x(b){return z(b)?M(e,E,"whitespace")(b):E(b)}function E(b){return b===124?f(b):b===null||T(b)?!o||r!==a?S(b):(e.exit("tableDelimiterRow"),e.exit("tableHead"),n(b)):S(b)}function S(b){return t(b)}function v(b){return e.enter("tableRow"),B(b)}function B(b){return b===124?(e.enter("tableCellDivider"),e.consume(b),e.exit("tableCellDivider"),B):b===null||T(b)?(e.exit("tableRow"),n(b)):z(b)?M(e,B,"whitespace")(b):(e.enter("data"),N(b))}function N(b){return b===null||b===124||U(b)?(e.exit("data"),B(b)):(e.consume(b),b===92?$:N)}function $(b){return b===92||b===124?(e.consume(b),N):N(b)}}function _u(e,n){let t=-1,i=!0,r=0,a=[0,0,0,0],o=[0,0,0,0],s=!1,l=0,u,c,h;const p=new bu;for(;++t<e.length;){const d=e[t],f=d[1];d[0]==="enter"?f.type==="tableHead"?(s=!1,l!==0&&(vi(p,n,l,u,c),c=void 0,l=0),u={type:"table",start:Object.assign({},f.start),end:Object.assign({},f.end)},p.add(t,0,[["enter",u,n]])):f.type==="tableRow"||f.type==="tableDelimiterRow"?(i=!0,h=void 0,a=[0,0,0,0],o=[0,t+1,0,0],s&&(s=!1,c={type:"tableBody",start:Object.assign({},f.start),end:Object.assign({},f.end)},p.add(t,0,[["enter",c,n]])),r=f.type==="tableDelimiterRow"?2:c?3:1):r&&(f.type==="data"||f.type==="tableDelimiterMarker"||f.type==="tableDelimiterFiller")?(i=!1,o[2]===0&&(a[1]!==0&&(o[0]=o[1],h=nn(p,n,a,r,void 0,h),a=[0,0,0,0]),o[2]=t)):f.type==="tableCellDivider"&&(i?i=!1:(a[1]!==0&&(o[0]=o[1],h=nn(p,n,a,r,void 0,h)),a=o,o=[a[1],t,0,0])):f.type==="tableHead"?(s=!0,l=t):f.type==="tableRow"||f.type==="tableDelimiterRow"?(l=t,a[1]!==0?(o[0]=o[1],h=nn(p,n,a,r,t,h)):o[1]!==0&&(h=nn(p,n,o,r,t,h)),r=0):r&&(f.type==="data"||f.type==="tableDelimiterMarker"||f.type==="tableDelimiterFiller")&&(o[3]=t)}for(l!==0&&vi(p,n,l,u,c),p.consume(n.events),t=-1;++t<n.events.length;){const d=n.events[t];d[0]==="enter"&&d[1].type==="table"&&(d[1]._align=vu(n.events,t))}return e}function nn(e,n,t,i,r,a){const o=i===1?"tableHeader":i===2?"tableDelimiter":"tableData",s="tableContent";t[0]!==0&&(a.end=Object.assign({},Be(n.events,t[0])),e.add(t[0],0,[["exit",a,n]]));const l=Be(n.events,t[1]);if(a={type:o,start:Object.assign({},l),end:Object.assign({},l)},e.add(t[1],0,[["enter",a,n]]),t[2]!==0){const u=Be(n.events,t[2]),c=Be(n.events,t[3]),h={type:s,start:Object.assign({},u),end:Object.assign({},c)};if(e.add(t[2],0,[["enter",h,n]]),i!==2){const p=n.events[t[2]],d=n.events[t[3]];if(p[1].end=Object.assign({},d[1].end),p[1].type="chunkText",p[1].contentType="text",t[3]>t[2]+1){const f=t[2]+1,w=t[3]-t[2]-1;e.add(f,w,[])}}e.add(t[3]+1,0,[["exit",h,n]])}return r!==void 0&&(a.end=Object.assign({},Be(n.events,r)),e.add(r,0,[["exit",a,n]]),a=void 0),a}function vi(e,n,t,i,r){const a=[],o=Be(n.events,t);r&&(r.end=Object.assign({},o),a.push(["exit",r,n])),i.end=Object.assign({},o),a.push(["exit",i,n]),e.add(t+1,0,a)}function Be(e,n){const t=e[n],i=t[0]==="enter"?"start":"end";return t[1][i]}const Au={name:"tasklistCheck",tokenize:Fu};function Cu(){return{text:{91:Au}}}function Fu(e,n,t){const i=this;return r;function r(l){return i.previous!==null||!i._gfmTasklistFirstContentOfListItem?t(l):(e.enter("taskListCheck"),e.enter("taskListCheckMarker"),e.consume(l),e.exit("taskListCheckMarker"),a)}function a(l){return U(l)?(e.enter("taskListCheckValueUnchecked"),e.consume(l),e.exit("taskListCheckValueUnchecked"),o):l===88||l===120?(e.enter("taskListCheckValueChecked"),e.consume(l),e.exit("taskListCheckValueChecked"),o):t(l)}function o(l){return l===93?(e.enter("taskListCheckMarker"),e.consume(l),e.exit("taskListCheckMarker"),e.exit("taskListCheck"),s):t(l)}function s(l){return T(l)?n(l):z(l)?e.check({tokenize:Eu},n,t)(l):t(l)}}function Eu(e,n,t){return M(e,i,"whitespace");function i(r){return r===null?t(r):n(r)}}function Su(e){return Ni([eu(),cu(),wu(e),Du(),Cu()])}const Tu={};function Iu(e){const n=this,t=e||Tu,i=n.data(),r=i.micromarkExtensions||(i.micromarkExtensions=[]),a=i.fromMarkdownExtensions||(i.fromMarkdownExtensions=[]),o=i.toMarkdownExtensions||(i.toMarkdownExtensions=[]);r.push(Su(t)),a.push(Q1()),o.push(X1(t))}const Bu=/[\0-\x1F!-,\.\/:-@\[-\^`\{-\xA9\xAB-\xB4\xB6-\xB9\xBB-\xBF\xD7\xF7\u02C2-\u02C5\u02D2-\u02DF\u02E5-\u02EB\u02ED\u02EF-\u02FF\u0375\u0378\u0379\u037E\u0380-\u0385\u0387\u038B\u038D\u03A2\u03F6\u0482\u0530\u0557\u0558\u055A-\u055F\u0589-\u0590\u05BE\u05C0\u05C3\u05C6\u05C8-\u05CF\u05EB-\u05EE\u05F3-\u060F\u061B-\u061F\u066A-\u066D\u06D4\u06DD\u06DE\u06E9\u06FD\u06FE\u0700-\u070F\u074B\u074C\u07B2-\u07BF\u07F6-\u07F9\u07FB\u07FC\u07FE\u07FF\u082E-\u083F\u085C-\u085F\u086B-\u089F\u08B5\u08C8-\u08D2\u08E2\u0964\u0965\u0970\u0984\u098D\u098E\u0991\u0992\u09A9\u09B1\u09B3-\u09B5\u09BA\u09BB\u09C5\u09C6\u09C9\u09CA\u09CF-\u09D6\u09D8-\u09DB\u09DE\u09E4\u09E5\u09F2-\u09FB\u09FD\u09FF\u0A00\u0A04\u0A0B-\u0A0E\u0A11\u0A12\u0A29\u0A31\u0A34\u0A37\u0A3A\u0A3B\u0A3D\u0A43-\u0A46\u0A49\u0A4A\u0A4E-\u0A50\u0A52-\u0A58\u0A5D\u0A5F-\u0A65\u0A76-\u0A80\u0A84\u0A8E\u0A92\u0AA9\u0AB1\u0AB4\u0ABA\u0ABB\u0AC6\u0ACA\u0ACE\u0ACF\u0AD1-\u0ADF\u0AE4\u0AE5\u0AF0-\u0AF8\u0B00\u0B04\u0B0D\u0B0E\u0B11\u0B12\u0B29\u0B31\u0B34\u0B3A\u0B3B\u0B45\u0B46\u0B49\u0B4A\u0B4E-\u0B54\u0B58-\u0B5B\u0B5E\u0B64\u0B65\u0B70\u0B72-\u0B81\u0B84\u0B8B-\u0B8D\u0B91\u0B96-\u0B98\u0B9B\u0B9D\u0BA0-\u0BA2\u0BA5-\u0BA7\u0BAB-\u0BAD\u0BBA-\u0BBD\u0BC3-\u0BC5\u0BC9\u0BCE\u0BCF\u0BD1-\u0BD6\u0BD8-\u0BE5\u0BF0-\u0BFF\u0C0D\u0C11\u0C29\u0C3A-\u0C3C\u0C45\u0C49\u0C4E-\u0C54\u0C57\u0C5B-\u0C5F\u0C64\u0C65\u0C70-\u0C7F\u0C84\u0C8D\u0C91\u0CA9\u0CB4\u0CBA\u0CBB\u0CC5\u0CC9\u0CCE-\u0CD4\u0CD7-\u0CDD\u0CDF\u0CE4\u0CE5\u0CF0\u0CF3-\u0CFF\u0D0D\u0D11\u0D45\u0D49\u0D4F-\u0D53\u0D58-\u0D5E\u0D64\u0D65\u0D70-\u0D79\u0D80\u0D84\u0D97-\u0D99\u0DB2\u0DBC\u0DBE\u0DBF\u0DC7-\u0DC9\u0DCB-\u0DCE\u0DD5\u0DD7\u0DE0-\u0DE5\u0DF0\u0DF1\u0DF4-\u0E00\u0E3B-\u0E3F\u0E4F\u0E5A-\u0E80\u0E83\u0E85\u0E8B\u0EA4\u0EA6\u0EBE\u0EBF\u0EC5\u0EC7\u0ECE\u0ECF\u0EDA\u0EDB\u0EE0-\u0EFF\u0F01-\u0F17\u0F1A-\u0F1F\u0F2A-\u0F34\u0F36\u0F38\u0F3A-\u0F3D\u0F48\u0F6D-\u0F70\u0F85\u0F98\u0FBD-\u0FC5\u0FC7-\u0FFF\u104A-\u104F\u109E\u109F\u10C6\u10C8-\u10CC\u10CE\u10CF\u10FB\u1249\u124E\u124F\u1257\u1259\u125E\u125F\u1289\u128E\u128F\u12B1\u12B6\u12B7\u12BF\u12C1\u12C6\u12C7\u12D7\u1311\u1316\u1317\u135B\u135C\u1360-\u137F\u1390-\u139F\u13F6\u13F7\u13FE-\u1400\u166D\u166E\u1680\u169B-\u169F\u16EB-\u16ED\u16F9-\u16FF\u170D\u1715-\u171F\u1735-\u173F\u1754-\u175F\u176D\u1771\u1774-\u177F\u17D4-\u17D6\u17D8-\u17DB\u17DE\u17DF\u17EA-\u180A\u180E\u180F\u181A-\u181F\u1879-\u187F\u18AB-\u18AF\u18F6-\u18FF\u191F\u192C-\u192F\u193C-\u1945\u196E\u196F\u1975-\u197F\u19AC-\u19AF\u19CA-\u19CF\u19DA-\u19FF\u1A1C-\u1A1F\u1A5F\u1A7D\u1A7E\u1A8A-\u1A8F\u1A9A-\u1AA6\u1AA8-\u1AAF\u1AC1-\u1AFF\u1B4C-\u1B4F\u1B5A-\u1B6A\u1B74-\u1B7F\u1BF4-\u1BFF\u1C38-\u1C3F\u1C4A-\u1C4C\u1C7E\u1C7F\u1C89-\u1C8F\u1CBB\u1CBC\u1CC0-\u1CCF\u1CD3\u1CFB-\u1CFF\u1DFA\u1F16\u1F17\u1F1E\u1F1F\u1F46\u1F47\u1F4E\u1F4F\u1F58\u1F5A\u1F5C\u1F5E\u1F7E\u1F7F\u1FB5\u1FBD\u1FBF-\u1FC1\u1FC5\u1FCD-\u1FCF\u1FD4\u1FD5\u1FDC-\u1FDF\u1FED-\u1FF1\u1FF5\u1FFD-\u203E\u2041-\u2053\u2055-\u2070\u2072-\u207E\u2080-\u208F\u209D-\u20CF\u20F1-\u2101\u2103-\u2106\u2108\u2109\u2114\u2116-\u2118\u211E-\u2123\u2125\u2127\u2129\u212E\u213A\u213B\u2140-\u2144\u214A-\u214D\u214F-\u215F\u2189-\u24B5\u24EA-\u2BFF\u2C2F\u2C5F\u2CE5-\u2CEA\u2CF4-\u2CFF\u2D26\u2D28-\u2D2C\u2D2E\u2D2F\u2D68-\u2D6E\u2D70-\u2D7E\u2D97-\u2D9F\u2DA7\u2DAF\u2DB7\u2DBF\u2DC7\u2DCF\u2DD7\u2DDF\u2E00-\u2E2E\u2E30-\u3004\u3008-\u3020\u3030\u3036\u3037\u303D-\u3040\u3097\u3098\u309B\u309C\u30A0\u30FB\u3100-\u3104\u3130\u318F-\u319F\u31C0-\u31EF\u3200-\u33FF\u4DC0-\u4DFF\u9FFD-\u9FFF\uA48D-\uA4CF\uA4FE\uA4FF\uA60D-\uA60F\uA62C-\uA63F\uA673\uA67E\uA6F2-\uA716\uA720\uA721\uA789\uA78A\uA7C0\uA7C1\uA7CB-\uA7F4\uA828-\uA82B\uA82D-\uA83F\uA874-\uA87F\uA8C6-\uA8CF\uA8DA-\uA8DF\uA8F8-\uA8FA\uA8FC\uA92E\uA92F\uA954-\uA95F\uA97D-\uA97F\uA9C1-\uA9CE\uA9DA-\uA9DF\uA9FF\uAA37-\uAA3F\uAA4E\uAA4F\uAA5A-\uAA5F\uAA77-\uAA79\uAAC3-\uAADA\uAADE\uAADF\uAAF0\uAAF1\uAAF7-\uAB00\uAB07\uAB08\uAB0F\uAB10\uAB17-\uAB1F\uAB27\uAB2F\uAB5B\uAB6A-\uAB6F\uABEB\uABEE\uABEF\uABFA-\uABFF\uD7A4-\uD7AF\uD7C7-\uD7CA\uD7FC-\uD7FF\uE000-\uF8FF\uFA6E\uFA6F\uFADA-\uFAFF\uFB07-\uFB12\uFB18-\uFB1C\uFB29\uFB37\uFB3D\uFB3F\uFB42\uFB45\uFBB2-\uFBD2\uFD3E-\uFD4F\uFD90\uFD91\uFDC8-\uFDEF\uFDFC-\uFDFF\uFE10-\uFE1F\uFE30-\uFE32\uFE35-\uFE4C\uFE50-\uFE6F\uFE75\uFEFD-\uFF0F\uFF1A-\uFF20\uFF3B-\uFF3E\uFF40\uFF5B-\uFF65\uFFBF-\uFFC1\uFFC8\uFFC9\uFFD0\uFFD1\uFFD8\uFFD9\uFFDD-\uFFFF]|\uD800[\uDC0C\uDC27\uDC3B\uDC3E\uDC4E\uDC4F\uDC5E-\uDC7F\uDCFB-\uDD3F\uDD75-\uDDFC\uDDFE-\uDE7F\uDE9D-\uDE9F\uDED1-\uDEDF\uDEE1-\uDEFF\uDF20-\uDF2C\uDF4B-\uDF4F\uDF7B-\uDF7F\uDF9E\uDF9F\uDFC4-\uDFC7\uDFD0\uDFD6-\uDFFF]|\uD801[\uDC9E\uDC9F\uDCAA-\uDCAF\uDCD4-\uDCD7\uDCFC-\uDCFF\uDD28-\uDD2F\uDD64-\uDDFF\uDF37-\uDF3F\uDF56-\uDF5F\uDF68-\uDFFF]|\uD802[\uDC06\uDC07\uDC09\uDC36\uDC39-\uDC3B\uDC3D\uDC3E\uDC56-\uDC5F\uDC77-\uDC7F\uDC9F-\uDCDF\uDCF3\uDCF6-\uDCFF\uDD16-\uDD1F\uDD3A-\uDD7F\uDDB8-\uDDBD\uDDC0-\uDDFF\uDE04\uDE07-\uDE0B\uDE14\uDE18\uDE36\uDE37\uDE3B-\uDE3E\uDE40-\uDE5F\uDE7D-\uDE7F\uDE9D-\uDEBF\uDEC8\uDEE7-\uDEFF\uDF36-\uDF3F\uDF56-\uDF5F\uDF73-\uDF7F\uDF92-\uDFFF]|\uD803[\uDC49-\uDC7F\uDCB3-\uDCBF\uDCF3-\uDCFF\uDD28-\uDD2F\uDD3A-\uDE7F\uDEAA\uDEAD-\uDEAF\uDEB2-\uDEFF\uDF1D-\uDF26\uDF28-\uDF2F\uDF51-\uDFAF\uDFC5-\uDFDF\uDFF7-\uDFFF]|\uD804[\uDC47-\uDC65\uDC70-\uDC7E\uDCBB-\uDCCF\uDCE9-\uDCEF\uDCFA-\uDCFF\uDD35\uDD40-\uDD43\uDD48-\uDD4F\uDD74\uDD75\uDD77-\uDD7F\uDDC5-\uDDC8\uDDCD\uDDDB\uDDDD-\uDDFF\uDE12\uDE38-\uDE3D\uDE3F-\uDE7F\uDE87\uDE89\uDE8E\uDE9E\uDEA9-\uDEAF\uDEEB-\uDEEF\uDEFA-\uDEFF\uDF04\uDF0D\uDF0E\uDF11\uDF12\uDF29\uDF31\uDF34\uDF3A\uDF45\uDF46\uDF49\uDF4A\uDF4E\uDF4F\uDF51-\uDF56\uDF58-\uDF5C\uDF64\uDF65\uDF6D-\uDF6F\uDF75-\uDFFF]|\uD805[\uDC4B-\uDC4F\uDC5A-\uDC5D\uDC62-\uDC7F\uDCC6\uDCC8-\uDCCF\uDCDA-\uDD7F\uDDB6\uDDB7\uDDC1-\uDDD7\uDDDE-\uDDFF\uDE41-\uDE43\uDE45-\uDE4F\uDE5A-\uDE7F\uDEB9-\uDEBF\uDECA-\uDEFF\uDF1B\uDF1C\uDF2C-\uDF2F\uDF3A-\uDFFF]|\uD806[\uDC3B-\uDC9F\uDCEA-\uDCFE\uDD07\uDD08\uDD0A\uDD0B\uDD14\uDD17\uDD36\uDD39\uDD3A\uDD44-\uDD4F\uDD5A-\uDD9F\uDDA8\uDDA9\uDDD8\uDDD9\uDDE2\uDDE5-\uDDFF\uDE3F-\uDE46\uDE48-\uDE4F\uDE9A-\uDE9C\uDE9E-\uDEBF\uDEF9-\uDFFF]|\uD807[\uDC09\uDC37\uDC41-\uDC4F\uDC5A-\uDC71\uDC90\uDC91\uDCA8\uDCB7-\uDCFF\uDD07\uDD0A\uDD37-\uDD39\uDD3B\uDD3E\uDD48-\uDD4F\uDD5A-\uDD5F\uDD66\uDD69\uDD8F\uDD92\uDD99-\uDD9F\uDDAA-\uDEDF\uDEF7-\uDFAF\uDFB1-\uDFFF]|\uD808[\uDF9A-\uDFFF]|\uD809[\uDC6F-\uDC7F\uDD44-\uDFFF]|[\uD80A\uD80B\uD80E-\uD810\uD812-\uD819\uD824-\uD82B\uD82D\uD82E\uD830-\uD833\uD837\uD839\uD83D\uD83F\uD87B-\uD87D\uD87F\uD885-\uDB3F\uDB41-\uDBFF][\uDC00-\uDFFF]|\uD80D[\uDC2F-\uDFFF]|\uD811[\uDE47-\uDFFF]|\uD81A[\uDE39-\uDE3F\uDE5F\uDE6A-\uDECF\uDEEE\uDEEF\uDEF5-\uDEFF\uDF37-\uDF3F\uDF44-\uDF4F\uDF5A-\uDF62\uDF78-\uDF7C\uDF90-\uDFFF]|\uD81B[\uDC00-\uDE3F\uDE80-\uDEFF\uDF4B-\uDF4E\uDF88-\uDF8E\uDFA0-\uDFDF\uDFE2\uDFE5-\uDFEF\uDFF2-\uDFFF]|\uD821[\uDFF8-\uDFFF]|\uD823[\uDCD6-\uDCFF\uDD09-\uDFFF]|\uD82C[\uDD1F-\uDD4F\uDD53-\uDD63\uDD68-\uDD6F\uDEFC-\uDFFF]|\uD82F[\uDC6B-\uDC6F\uDC7D-\uDC7F\uDC89-\uDC8F\uDC9A-\uDC9C\uDC9F-\uDFFF]|\uD834[\uDC00-\uDD64\uDD6A-\uDD6C\uDD73-\uDD7A\uDD83\uDD84\uDD8C-\uDDA9\uDDAE-\uDE41\uDE45-\uDFFF]|\uD835[\uDC55\uDC9D\uDCA0\uDCA1\uDCA3\uDCA4\uDCA7\uDCA8\uDCAD\uDCBA\uDCBC\uDCC4\uDD06\uDD0B\uDD0C\uDD15\uDD1D\uDD3A\uDD3F\uDD45\uDD47-\uDD49\uDD51\uDEA6\uDEA7\uDEC1\uDEDB\uDEFB\uDF15\uDF35\uDF4F\uDF6F\uDF89\uDFA9\uDFC3\uDFCC\uDFCD]|\uD836[\uDC00-\uDDFF\uDE37-\uDE3A\uDE6D-\uDE74\uDE76-\uDE83\uDE85-\uDE9A\uDEA0\uDEB0-\uDFFF]|\uD838[\uDC07\uDC19\uDC1A\uDC22\uDC25\uDC2B-\uDCFF\uDD2D-\uDD2F\uDD3E\uDD3F\uDD4A-\uDD4D\uDD4F-\uDEBF\uDEFA-\uDFFF]|\uD83A[\uDCC5-\uDCCF\uDCD7-\uDCFF\uDD4C-\uDD4F\uDD5A-\uDFFF]|\uD83B[\uDC00-\uDDFF\uDE04\uDE20\uDE23\uDE25\uDE26\uDE28\uDE33\uDE38\uDE3A\uDE3C-\uDE41\uDE43-\uDE46\uDE48\uDE4A\uDE4C\uDE50\uDE53\uDE55\uDE56\uDE58\uDE5A\uDE5C\uDE5E\uDE60\uDE63\uDE65\uDE66\uDE6B\uDE73\uDE78\uDE7D\uDE7F\uDE8A\uDE9C-\uDEA0\uDEA4\uDEAA\uDEBC-\uDFFF]|\uD83C[\uDC00-\uDD2F\uDD4A-\uDD4F\uDD6A-\uDD6F\uDD8A-\uDFFF]|\uD83E[\uDC00-\uDFEF\uDFFA-\uDFFF]|\uD869[\uDEDE-\uDEFF]|\uD86D[\uDF35-\uDF3F]|\uD86E[\uDC1E\uDC1F]|\uD873[\uDEA2-\uDEAF]|\uD87A[\uDFE1-\uDFFF]|\uD87E[\uDE1E-\uDFFF]|\uD884[\uDF4B-\uDFFF]|\uDB40[\uDC00-\uDCFF\uDDF0-\uDFFF]/g,qu=Object.hasOwnProperty;class Ru{constructor(){this.occurrences,this.reset()}slug(n,t){const i=this;let r=Pu(n,t===!0);const a=r;for(;qu.call(i.occurrences,r);)i.occurrences[a]++,r=a+"-"+i.occurrences[a];return i.occurrences[r]=0,r}reset(){this.occurrences=Object.create(null)}}function Pu(e,n){return typeof e!="string"?"":(n||(e=e.toLowerCase()),e.replace(Bu,"").replace(/ /g,"-"))}function zu(e){const n=e.type==="element"?e.tagName.toLowerCase():"",t=n.length===2&&n.charCodeAt(0)===104?n.charCodeAt(1):0;return t>48&&t<55?t-48:void 0}function Lu(e){return"children"in e?Pr(e):"value"in e?e.value:""}function Ou(e){return e.type==="text"?e.value:"children"in e?Pr(e):""}function Pr(e){let n=-1;const t=[];for(;++n<e.children.length;)t[n]=Ou(e.children[n]);return t.join("")}const Mu={},Di=new Ru;function Nu(e){const t=(e||Mu).prefix||"";return function(i){Di.reset(),yn(i,"element",function(r){zu(r)&&!r.properties.id&&(r.properties.id=t+Di.slug(Lu(r)))})}}function Hu({children:e,productSlug:n}){return L.jsx("div",{className:"md",children:L.jsx(pl,{remarkPlugins:[Iu],rehypePlugins:[Nu],components:{a({href:t="",children:i,...r}){const a=Kr(t,n);if(a)return L.jsx(Ai,{to:a,children:i});if(t.startsWith("#"))return L.jsx("a",{href:t,...r,children:i});if(!/^https?:/.test(t)){const o=t.replace(/^\.\.?\//,"");return L.jsx("a",{href:`https://github.com/avcool3/hone/blob/main/${o}`,target:"_blank",rel:"noreferrer",children:i})}return L.jsx("a",{href:t,target:"_blank",rel:"noreferrer",...r,children:i})},table({children:t}){return L.jsx("div",{className:"tscroll",children:L.jsx("table",{children:t})})}},children:e})})}const ju=`# Adaptive elicitation (DOSE)

## Why replace a working questionnaire

The Holt-Laury Multiple Price List is a good instrument. Hone's problem
with it was never validity — it was that thirty questions is a wall, and
it sits at the very front of the funnel, before the user has seen
anything the product does.

There is also a substantive problem, and it is the more interesting one.
The classic menu's indifference points top out around γ ≈ 1.4. Above
that, **every row is answered the same way**, so a genuinely risk-averse
user — tier 35 and up, a third of Hone's scale — produces a choice vector
that is consistent with any γ from 1.5 to 5. The MLE then reports a
number, and that number is mostly noise.

Chapman, Snowberg, Wang and Camerer (2018) set out the alternative:
maintain a Bayesian posterior over the preference parameters and, at each
step, ask whichever question the posterior expects to learn the most
from. They found a handful of adaptive questions recovers parameters
about as precisely as a full menu, with better test-retest reliability —
partly because subjects who are still paying attention give better data.

## Method

**Posterior** over a 121 × 13 grid in (γ, μ). μ is the same Fechner noise
parameter the MLE estimates: a user's inconsistency is information about
how much to trust their answers, not an error to discard.

**Likelihood** is \`hone.risk_profile.estimation.choice_probability\` under
the contextual-Fechner specification — the same function the MLE uses.
The grid version is vectorized for speed and held to agreement with it by
a test, because the two estimators drifting apart would mean two
different models of the same person.

**Selection** maximizes the mutual information between the parameters and
the answer:

\`\`\`
I(θ; y) = H( E_θ[Pr(A|θ)] ) − E_θ[ H(Pr(A|θ)) ]
\`\`\`

with H the binary entropy in bits. The first term rewards questions the
posterior is undecided about; the second penalizes questions that are
coin flips *for every individual θ* (those teach nothing about γ, only
about μ). A question everyone answers the same way scores zero and is
never asked.

**The question bank** is constructed rather than curated. For each target
γ on a grid and each of four coin flips, the sure amount offered is that
γ's certainty equivalent — which has a closed form, so the bank's
indifference points tile the range −1.2 to 4.8 with no gap wider than
0.5. A bank with holes cannot separate the tiers it fails to reach,
however cleverly questions are then selected. Pairs where one option
dominates are dropped: they cost a user's attention and buy nothing.

**A diversity rule** keeps consecutive questions from reusing the same
gamble. Pure information-maximization asks the same coin flip six times
with the sure amount nudged each round, which is tedious and reads like
the tool is haggling. Accepting a question within 80% of the best
expected gain fixes it at no measured cost in accuracy (mean RMSE 0.353
with and without, across γ from −0.5 to 3.6).

**Stopping** at eight questions, or earlier if the posterior s.d. on γ
drops below 0.05 — but never before four answers, because an early tight
posterior is the prior talking, not the user.

## Does it work

Synthetic CRRA subjects with Fechner noise (μ = 0.10), 20 runs per cell,
RMSE of the recovered γ:

| True γ | DOSE, 8 questions | DOSE, 12 questions | Full menu, 30 questions |
|---|---|---|---|
| −0.5 | 0.28 | 0.23 | 0.24 |
| +0.3 | 0.21 | 0.24 | 0.20 |
| +1.2 | 0.22 | 0.17 | 0.31 |
| +2.5 | **0.37** | 0.28 | **1.92** |
| +3.6 | **0.52** | 0.39 | **1.50** |

Eight adaptive questions match thirty fixed ones where the fixed menu can
see, and beat it by a factor of four to five where it cannot. The bottom
two rows are the substantive result: they are not a marginal efficiency
gain, they are the difference between measuring a risk-averse user and
guessing at them.

Reproduce with \`tests/test_dose.py::TestPosterior::test_beats_the_full_menu_where_the_menu_is_blind\`.

## What it does not fix

* **Eight binary answers carry at most eight bits.** The posterior s.d.
  after a full run is typically 0.3–0.7, which spans several of the 50
  tiers. The interval is shown on the profile page and carried through as
  a credible interval rather than being quietly rounded away — γ is
  inferred, not observed, and everything downstream inherits that width.
* **The estimate is Bayesian**, so it is pulled toward the prior. At the
  extremes this is visible: a true γ of 3.6 recovers at about 3.2 after
  eight questions. Widening the prior reduces the bias and costs a little
  precision in the middle, where most users are; the current setting
  (mean 0.65, s.d. 1.60) takes that trade deliberately.
* **Hypothetical stakes.** These are unincentivized questions about money
  the user will not receive, which is a known weakness of the whole
  elicitation literature and not something an adaptive design repairs.
  The revealed-γ diagnostic on the portfolio page — which infers risk
  aversion from what someone *actually holds* — is the counterweight, and
  the two disagreeing is a finding worth showing rather than hiding.
* **Preferences drift.** A measurement is of a moment. Hone suggests
  re-taking it quarterly.

## References

* Chapman, J., Snowberg, E., Wang, S., & Camerer, C. (2018). "Loss
  Attitudes in the U.S. Population: Evidence from Dynamically Optimized
  Sequential Experimentation (DOSE)." NBER Working Paper 25072.
* Holt, C. A., & Laury, S. K. (2002). "Risk aversion and incentive
  effects." *American Economic Review* 92(5), 1644–1655.
* Wilcox, N. T. (2011). "'Stochastically more risk averse': a contextual
  theory of stochastic discrete choice under risk." *Journal of
  Econometrics* 162(1), 89–104.
* Lindley, D. V. (1956). "On a measure of the information provided by an
  experiment." *Annals of Mathematical Statistics* 27(4), 986–1005.
`,Uu=`# Do convictions actually help? A comparative backtest

The Conviction Compiler turns a plain-English thesis into a structured
view, and the confidence attached to that view is what scales how far
Black-Litterman tilts the portfolio away from equilibrium. That number is
self-reported, unverified, and multiplied straight into position sizes.
\`hone/journal/\` now scores that number against outcomes and rescales it
before it reaches Black-Litterman. This document asks whether any of that
machinery — the views, the confidence channel, the calibration — actually
earns its place, and for whom.

This document reports a walk-forward simulation over a *population* of
investors who differ in risk aversion (γ) and in genuine forecasting
skill. Code: \`hone/backtest/conviction.py\`; tests:
\`tests/test_conviction_backtest.py\`; sweep runner:
\`research/conviction/run_conviction_backtest.py\`.

---

## Headline

1. **Skill is the whole story. Confidence is a rounding error.** Whether a
   user's convictions help is determined almost entirely by whether their
   forecasts contain information. How that information is weighted —
   self-reported confidence, calibrated confidence, or no confidence
   channel at all — moves median Sharpe by ≤ 0.05 in the shipped
   configuration, against a 0.16 gap between "has skill" and "doesn't".
2. **Calibrated confidence did not beat stated confidence.** Replacing the
   user's self-report with their realized hit rate won on **27-54%** of
   investor draws in equities and **26-41%** in crypto — i.e. it lost
   more often than it won everywhere except the zero-skill equities cell.
   It helps the no-skill and the overconfident; it taxes anyone with real
   edge, because a Beta-smoothed hit rate is a slow, noisy estimator that
   caps confidence around 0.23 even for a genuinely good forecaster.
3. **A zero-skill user is made slightly worse off by using views at all.**
   In equities, views beat the view-free portfolio on only **33-48%** of
   draws at skill 0, at every γ. The product currently has no way to tell
   those users apart from the skilled ones.
4. **Taking views at face value is not catastrophic today — but only
   because the 35% position cap is hiding it.** Remove the cap and a
   no-skill user's face-value portfolio drops from Sharpe 0.394
   (view-free) to **0.184**, with an effective breadth of **1.28 names**.
   The cap, not Idzorek's Ω, is currently doing the safety work.
5. **Crypto is more favourable to views than equities**, but for an
   uncomfortable reason: the crypto baseline (\`risk_only\`) is weaker
   there, so there is more to beat.

---

## 1. What was compared

On the same price history, per investor draw:

| strategy | what it is |
|---|---|
| \`equal_weight\` | 1/N — the retail default |
| \`market_hold\` | buy and hold the market proxy (SPY / BTC/USD) |
| \`risk_only\` | Hone's γ-aware MVO on the equilibrium prior, no views |
| \`views_stated_conf\` | the full pipeline at the user's **self-reported** confidence — what Hone ships |
| \`views_calibrated_conf\` | identical views, confidence **replaced outright** by the user's realized hit rate to date |
| \`views_full_conf\` | views taken at **face value** (confidence = 1.0) — the naive "the LLM said so" wiring |

Strategies 4-6 receive byte-identical views. Only Ω differs, so any gap
between them is attributable to the confidence mapping and nothing else.
(\`tests/test_conviction_backtest.py::test_only_omega_differs_between_view_strategies\`
pins this: set stated confidence to 1.0 and the stated and face-value
equity curves coincide exactly.)

## 2. Method

**Walk-forward.** 252-day (365 for crypto) trailing estimation window,
rebalanced every 21 periods, Ledoit-Wolf shrinkage covariance,
Sharpe-calibrated δ, 1/N equilibrium prior, long-only, 35% per-name cap.
Every weight at date *t* is a function of data strictly before *t*.

**The investor's skill** is the information coefficient: the correlation
between their forecast and the realized forward return over the view
horizon (63 periods, re-issued every 21). At the decision date the
simulator — not the investor — standardizes the realized forward return
against the equilibrium prior and hands the investor
\`skill × signal + √(1-skill²) × noise\`. Centering the noise on the
*prior* rather than on zero makes skill = 0 a clean null: unbiased noise
around what the model already believed, rather than a systematic drag
toward minimum variance.

Skill translates to directional accuracy as
\`hit_rate = 0.5 + arcsin(ρ)/π\`, which is worth internalizing: an
information coefficient of **0.4 — better than most professionals ever
achieve — is a 63% hit rate**, not 80%.

**Stated confidence** is anchored where humans actually speak. The
compiler's own prompt maps hedged language to 30-45% and emphatic
language to 70-85%; nobody types "3% confident". So
\`stated = clip(overconfidence × (0.30 + 0.70 × true_edge))\`. A
calibrated no-skill investor still says 31%; a 2×-overconfident one says
63%.

**Calibrated confidence** is \`2 × (hit_rate − 0.5)\`, floored at 0.02,
where the hit rate is the investor's own resolved views to date,
Beta-smoothed with 5 pseudo-observations at chance. Views resolve only
after their horizon elapses, so there is no look-ahead.

This is deliberately the *aggressive* form of calibration: it throws the
user's number away and substitutes the measurement. What \`hone/journal/\`
actually ships is gentler — a logistic rescaling of the stated confidence
in log-odds space, shrunk toward the identity with 20 pseudo-counts,
inert below 5 resolutions and clipped to [0.05, 0.95]. The shipped
behaviour therefore sits *between* the \`views_stated_conf\` and
\`views_calibrated_conf\` arms measured here, and those two arms bracket
it. §9 reads the results back onto that design.

**Design.** 40 investor draws × 5 γ ∈ {0.5, 1.2, 2.5, 5.0, 8.0} × 3 skill
∈ {0, 0.2, 0.4} × 2 overconfidence ∈ {1×, 2×} × 2 asset classes = 14,400
investor-cell runs. The price path *and* the forecast-noise stream are
keyed to the investor index alone, so the design is paired: γ and skill
never change which market the investor lived through. Win rates are
computed per draw, not on pooled averages — a strategy that wins on
average but loses for 60% of users is a bad product.

**What is synthetic.** Prices come from \`synthetic_universe\` and
\`synthetic_crypto_universe\`. These are Gaussian (Student-t for crypto)
panels with constant covariance and drifts drawn *independently of
volatility*. §6 explains why that matters and re-runs the key result on a
DGP where risk is compensated.

---

## 3. Results — equities

40 draws, pooled across all five γ, calibrated stater (overconfidence
1×). Medians; \`beat_*\` is the fraction of the 200 draw-γ pairs in which
the strategy beat the benchmark on Sharpe.

| skill | strategy | CAGR | vol | Sharpe | Sortino | max DD | eff. N | turnover | beat risk_only | beat market_hold |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.0 | equal_weight | 0.123 | 0.226 | 0.469 | 0.785 | −0.286 | 6.00 | 0.00 | 0.525 | 0.700 |
| 0.0 | market_hold | 0.123 | 0.337 | 0.429 | 0.718 | −0.428 | 1.00 | 0.00 | 0.360 | — |
| 0.0 | risk_only | 0.117 | 0.214 | 0.458 | 0.780 | −0.307 | 3.97 | 0.02 | — | 0.640 |
| 0.0 | stated | 0.119 | 0.231 | 0.448 | 0.748 | −0.310 | 3.66 | 0.38 | **0.430** | 0.610 |
| 0.0 | calibrated | 0.117 | 0.220 | 0.445 | 0.750 | −0.306 | 3.93 | 0.14 | 0.415 | 0.620 |
| 0.0 | face_value | 0.118 | 0.238 | 0.420 | 0.705 | −0.324 | 3.28 | 0.46 | 0.435 | 0.585 |
| 0.2 | stated | 0.138 | 0.233 | 0.522 | 0.881 | −0.298 | 3.61 | 0.40 | **0.650** | 0.720 |
| 0.2 | calibrated | 0.131 | 0.227 | 0.507 | 0.859 | −0.303 | 3.83 | 0.25 | 0.650 | 0.700 |
| 0.2 | face_value | 0.131 | 0.239 | 0.469 | 0.796 | −0.313 | 3.29 | 0.45 | 0.610 | 0.690 |
| 0.4 | stated | 0.165 | 0.234 | 0.621 | 1.059 | −0.289 | 3.53 | 0.40 | **0.830** | 0.830 |
| 0.4 | calibrated | 0.156 | 0.229 | 0.594 | 1.005 | −0.289 | 3.75 | 0.31 | 0.830 | 0.815 |
| 0.4 | face_value | 0.169 | 0.238 | 0.604 | 1.005 | −0.298 | 3.30 | 0.44 | 0.805 | 0.800 |

At 2× overconfidence the only row that moves is \`stated\`: Sharpe falls
from 0.448 → 0.424 (skill 0), 0.522 → 0.473 (skill 0.2), 0.621 → 0.605
(skill 0.4). Doubling a user's stated confidence costs at most ~0.05
Sharpe.

## 4. Results — crypto

Same design, 365-day annualization, BTC/USD proxy, 1,460-day panels.

| skill | strategy | CAGR | vol | Sharpe | Sortino | max DD | eff. N | turnover | beat risk_only | beat market_hold |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.0 | equal_weight | 0.302 | 0.725 | 0.667 | 1.092 | −0.680 | 6.00 | 0.00 | 0.650 | 0.800 |
| 0.0 | market_hold | 0.155 | 0.541 | 0.465 | 0.657 | −0.632 | 1.00 | 0.00 | 0.240 | — |
| 0.0 | risk_only | 0.240 | 0.603 | 0.592 | 0.940 | −0.646 | 3.21 | 0.01 | — | 0.760 |
| 0.0 | stated | 0.294 | 0.716 | 0.658 | 1.026 | −0.681 | 3.24 | 0.39 | **0.565** | 0.745 |
| 0.0 | calibrated | 0.287 | 0.643 | 0.657 | 1.025 | −0.664 | 3.30 | 0.21 | 0.575 | 0.755 |
| 0.0 | face_value | 0.262 | 0.743 | 0.633 | 0.979 | −0.692 | 3.14 | 0.45 | 0.580 | 0.780 |
| 0.2 | stated | 0.378 | 0.724 | 0.744 | 1.174 | −0.661 | 3.22 | 0.40 | **0.790** | 0.820 |
| 0.2 | calibrated | 0.355 | 0.670 | 0.729 | 1.130 | −0.651 | 3.30 | 0.29 | 0.730 | 0.785 |
| 0.2 | face_value | 0.347 | 0.740 | 0.718 | 1.132 | −0.663 | 3.13 | 0.44 | 0.735 | 0.840 |
| 0.4 | stated | 0.446 | 0.728 | 0.820 | 1.305 | −0.642 | 3.21 | 0.39 | **0.915** | 0.855 |
| 0.4 | calibrated | 0.423 | 0.687 | 0.800 | 1.246 | −0.632 | 3.27 | 0.33 | 0.880 | 0.855 |
| 0.4 | face_value | 0.464 | 0.737 | 0.835 | 1.317 | −0.640 | 3.13 | 0.43 | 0.915 | 0.870 |

The crypto picture looks friendlier to views at every skill level, but
note *why*: \`risk_only\` there posts Sharpe 0.592 against 1/N's 0.667. The
equilibrium prior does worse in crypto, so views have a weaker baseline
to beat. This is a statement about the baseline, not about the views.

## 5. Does confidence calibration matter?

Paired per draw — the fraction of investor draws in which the left-hand
strategy beat the right-hand one on Sharpe. 0.500 means a coin flip.

**Equities**

| skill | overconf. | calibrated > stated | stated > face_value | calibrated > face_value | stated > risk_only |
|---|---|---|---|---|---|
| 0.0 | 1× | 0.540 | 0.555 | 0.570 | 0.430 |
| 0.0 | 2× | 0.555 | 0.500 | 0.570 | 0.420 |
| 0.2 | 1× | 0.370 | 0.555 | 0.455 | 0.650 |
| 0.2 | 2× | 0.425 | 0.525 | 0.455 | 0.640 |
| 0.4 | 1× | 0.270 | 0.575 | 0.380 | 0.830 |
| 0.4 | 2× | 0.380 | 0.555 | 0.380 | 0.815 |

**Crypto**

| skill | overconf. | calibrated > stated | stated > face_value | calibrated > face_value | stated > risk_only |
|---|---|---|---|---|---|
| 0.0 | 1× | 0.410 | 0.470 | 0.440 | 0.565 |
| 0.0 | 2× | 0.395 | 0.500 | 0.440 | 0.605 |
| 0.2 | 1× | 0.290 | 0.520 | 0.415 | 0.790 |
| 0.2 | 2× | 0.390 | 0.540 | 0.415 | 0.770 |
| 0.4 | 1× | 0.265 | 0.470 | 0.355 | 0.915 |
| 0.4 | 2× | 0.345 | 0.510 | 0.355 | 0.915 |

Read plainly:

- **Calibration loses.** The only cell where calibrated confidence beats
  stated confidence more often than not is zero-skill equities (0.540 /
  0.555) — and there the entire strategy is under water versus
  \`risk_only\` anyway. At skill 0.4 calibration wins only 27% of draws.
- **Calibration does exactly what it is supposed to do; that is the
  problem.** Measured hit rates come out at 0.511 / 0.580 / 0.640 for
  skill 0 / 0.2 / 0.4, so calibrated confidence lands at 0.07 / 0.15 /
  0.23. A genuinely skilled user's views get 23% weight instead of the
  48% they asked for, and the portfolio stays too close to equilibrium to
  capture the edge they actually have.
- **The overconfidence case is where it earns something.** Every
  \`calibrated > stated\` figure rises when the user is 2× overconfident
  (0.270 → 0.380, 0.290 → 0.390). Calibration is insurance against
  miscalibration, not a performance improvement.
- **The confidence channel as a whole is weak.** \`stated > face_value\` sits
  at 0.47-0.58 across every cell in both asset classes — statistically
  indistinguishable from a coin flip on 40 draws. In the shipped
  configuration, the difference between a carefully elicited confidence
  and no confidence model at all is close to nothing.

## 6. Does the answer depend on γ?

Median Sharpe by γ, equities, calibrated stater:

| skill | γ | risk_only | stated | calibrated | face_value |
|---|---|---|---|---|---|
| 0.0 | 0.5 | 0.468 | 0.421 | 0.409 | 0.406 |
| 0.0 | 1.2 | 0.450 | 0.411 | 0.382 | 0.435 |
| 0.0 | 2.5 | 0.471 | 0.437 | 0.456 | 0.424 |
| 0.0 | 5.0 | 0.468 | 0.457 | 0.511 | 0.420 |
| 0.0 | 8.0 | 0.448 | 0.467 | 0.523 | 0.442 |
| 0.4 | 0.5 | 0.468 | 0.548 | 0.545 | 0.557 |
| 0.4 | 1.2 | 0.450 | 0.598 | 0.592 | 0.603 |
| 0.4 | 2.5 | 0.471 | 0.601 | 0.604 | 0.605 |
| 0.4 | 5.0 | 0.468 | 0.639 | 0.622 | 0.596 |
| 0.4 | 8.0 | 0.448 | 0.659 | 0.620 | 0.668 |

\`beat_risk_only\` for \`stated\` in equities rises monotonically with γ at
skill 0.4: 0.800, 0.775, 0.825, 0.850, **0.900**. At skill 0 it stays flat
and below chance at every γ: 0.475, 0.400, 0.400, 0.425, 0.450.

There is one genuine γ effect, and it is the sensible one: **the more
risk-averse the investor, the more the confidence discount is worth.** At
zero skill, calibrated confidence goes from the *worst* view strategy at
γ = 0.5 (0.409 vs \`risk_only\`'s 0.468) to the best at γ = 5 and γ = 8
(0.511 vs 0.468, and 0.523 vs 0.448 — the only view strategy clearly
above the baseline at both). A high-γ investor is the one most damaged by
having noise injected into μ, so muting the noise is worth most to them.
Crypto shows the same tendency more weakly and noisily.

## 7. Robustness checks

### 7.1 The synthetic DGP is unfair to \`risk_only\`

\`synthetic_universe\` draws each asset's drift independently of its
volatility. Hone's equilibrium prior is \`Π = δ Σ w\`, which asserts the
opposite: more covariance with the market means more expected return. The
prior is therefore *misspecified by construction* in the default panels,
and \`risk_only\`'s mediocre showing versus 1/N (it wins 47.5% of draws) is
partly an artefact.

Re-running the key slice on a panel where every asset prices at the same
0.40 Sharpe (\`research/conviction/sensitivity_dgp.py\`, 24 draws, γ ∈ {1.2, 2.5,
8.0}):

| skill | strategy | Sharpe | CAGR | eff. N | beat risk_only |
|---|---|---|---|---|---|
| 0.0 | equal_weight | 0.680 | 0.174 | 6.00 | 0.583 |
| 0.0 | risk_only | 0.681 | 0.168 | 4.43 | — |
| 0.0 | stated | 0.674 | 0.170 | 3.65 | 0.389 |
| 0.0 | calibrated | 0.665 | 0.161 | 4.10 | 0.292 |
| 0.0 | face_value | 0.654 | 0.170 | 3.27 | 0.417 |
| 0.2 | stated | 0.776 | 0.207 | 3.60 | 0.569 |
| 0.2 | calibrated | 0.714 | 0.195 | 3.82 | 0.583 |
| 0.2 | face_value | 0.744 | 0.208 | 3.26 | 0.639 |
| 0.4 | stated | 0.868 | 0.235 | 3.53 | 0.778 |
| 0.4 | calibrated | 0.834 | 0.214 | 3.72 | 0.736 |
| 0.4 | face_value | 0.846 | 0.235 | 3.28 | 0.764 |

\`risk_only\` now ties 1/N exactly (0.681 vs 0.680), confirming the
artefact. Every qualitative conclusion survives: zero-skill views are
mildly harmful (29-42% win rate), calibration still trails stated
confidence at positive skill, and the spread across confidence treatments
stays small relative to the spread across skill. The crypto cell where
zero-skill views appeared to *help* does not survive — treat that as a
baseline artefact, not a finding.

### 7.2 The 35% position cap is doing the safety work

One slice (equities, γ = 2.5, 24 draws) at the shipped cap and with the
cap removed (\`research/conviction/sensitivity_cap.py\`):

| cap | skill | strategy | Sharpe | CAGR | eff. N | turnover |
|---|---|---|---|---|---|---|
| 0.35 | 0.0 | risk_only | 0.390 | 0.101 | 5.38 | 0.01 |
| 0.35 | 0.0 | stated | 0.358 | 0.102 | 3.75 | 0.42 |
| 0.35 | 0.0 | calibrated | 0.407 | 0.110 | 4.80 | 0.18 |
| 0.35 | 0.0 | face_value | 0.367 | 0.106 | 3.27 | 0.48 |
| **1.00** | 0.0 | risk_only | 0.394 | 0.102 | 5.38 | 0.01 |
| **1.00** | 0.0 | stated | **0.231** | 0.069 | 2.07 | 0.69 |
| **1.00** | 0.0 | calibrated | **0.351** | 0.095 | 4.45 | 0.23 |
| **1.00** | 0.0 | face_value | **0.184** | 0.055 | 1.28 | 0.77 |
| 1.00 | 0.4 | stated | 0.665 | 0.190 | 1.70 | 0.72 |
| 1.00 | 0.4 | calibrated | 0.607 | 0.167 | 2.69 | 0.58 |
| 1.00 | 0.4 | face_value | 0.597 | 0.180 | 1.29 | 0.77 |

Uncapped, a no-skill user's face-value portfolio is a **1.28-name bet**
that loses **53% of the view-free Sharpe** (0.184 vs 0.394) and 4.7
percentage points of annual return. Calibrated confidence is the only
treatment that keeps such a user near the view-free baseline (0.351,
effective breadth 4.45). Two things follow: the cap is currently
substituting for a confidence model, and **the value of calibration is
conditional on how tightly the portfolio is otherwise constrained** — it
is worth far more for a concentrated book than for a capped six-name one.

### 7.3 \`View.expected_return\` explodes on short horizons

A view is a target price plus a horizon; \`View.expected_return\`
annualizes it as a CAGR. Over 10 seeds of zero-skill quarterly targets:

| asset class | mean implied return | median | > +100%/yr | > +1000%/yr | max |
|---|---|---|---|---|---|
| equities | +27%/yr | +4%/yr | 13% | 0.0% | +900%/yr |
| crypto | +962%/yr | +19%/yr | 40% | 12% | +130,300%/yr |

The median is sane; the tail is not. Exponentiating a noisy quarterly
return to an annual rate is explosive in high-volatility assets, and 12%
of crypto convictions produce a Q entry above +1000%/yr. At full
confidence these go straight into μ and pin the optimizer against its
bound. This is a live product hazard independent of everything else in
this document: a user who types a plausible three-month BTC target can
generate an expected-return input that no risk model should be asked to
digest.

### 7.4 Costs are not charged

The backtest is frictionless. One-way turnover per rebalance is 0.02 for
\`risk_only\` versus 0.38-0.46 for the view strategies — roughly **4.8×
book turnover per year** against 0.2×. At 10bp per side that is ~0.48%/yr
for stated confidence and ~0.02%/yr for \`risk_only\`. That fee is
comfortably covered at skill 0.4 (+4.8pp CAGR), roughly half-eaten at
skill 0.2 (+2.1pp), and pure loss at skill 0. Calibrated confidence cuts
turnover by 45-63% for low-skill users, which is a real advantage the
frictionless Sharpe comparison above does not credit it for.

---

## 8. Honest reading

**Where Hone's machinery clearly helps.** A user with a genuine
information coefficient of 0.2-0.4 is better off running their views
through Black-Litterman + MVO than not: +2.1 to +4.8 percentage points of
CAGR in equities, +0.06 to +0.16 Sharpe, winning on 65-83% of draws in
equities and 79-92% in crypto, with no increase in drawdown. That is a
real and reasonably robust result, and it holds at every γ tested.

**Where it does not help.** For a user with no edge — which, given that
an IC of 0.2 is professional-grade, is most users — views are a small
negative in equities (win rate 0.33-0.48 versus the view-free portfolio at
every γ) and a wash after costs. The product cannot presently distinguish
these users from skilled ones, and the confidence they self-report does
not distinguish them either: a no-skill investor and a skilled one both
say something in the 30-50% band.

**Where the specific claim about confidence fails.** The Idzorek
confidence channel is close to inert as shipped. Stated confidence beats
face value on 47-58% of draws — a coin flip. Doubling every user's stated
confidence costs at most 0.05 Sharpe. The 35% cap and the long-only
constraint are absorbing what Ω was supposed to absorb. If this project's
pitch is "your confidence sizes the tilt", the honest version is "your
confidence sizes the tilt within bounds that already do most of the
work".

**Where calibration fails.** Replacing self-reported confidence with a
realized hit rate is not a free improvement. It loses to self-report on
63-74% of draws for skilled users, because a Beta-smoothed directional hit
rate is a low-power estimator: after ~90 resolved views, a true IC of 0.4
still only reads as 0.64 accuracy, mapping to 0.23 confidence. The
correction is right in direction and far too blunt in magnitude.

**A trap the journal walks into.** The naive scoring metric — "you said
up, it went up" — is contaminated by drift, and \`resolve_prediction\`'s
\`direction_hit\` is exactly that metric. See §9.

**Limits of this evidence.** Synthetic Gaussian/Student-t prices with
constant covariance and no regime shifts; no transaction costs, taxes, or
slippage; one view horizon (63 periods) and two views per rebalance; skill
modelled as a stationary information coefficient with independent
per-asset noise, whereas real conviction errors are correlated across
names and clustered in time (everyone is wrong about the same thing at the
same moment, which is when it hurts most); 40 draws, so win rates carry a
standard error of roughly ±8pp and differences under ~15pp should not be
over-read. Nothing here has been validated on real price history.

---

## 9. Reading this back onto \`hone/journal/\`

The journal and its Brier calibration landed alongside this backtest, and
\`apply_calibration\` is already wired into the rebalance endpoint. The
results say the shipped design got the important call right and leave
three concrete corrections.

**The gentle design is the correct one.** Full replacement of stated
confidence by a measured hit rate — the \`views_calibrated_conf\` arm — is a
*net negative* for anyone with real edge, losing on 63-74% of draws at
skill 0.2-0.4. What ships instead is a logistic rescale shrunk toward the
identity with 20 pseudo-counts, which moves a user only part of the way
toward the measurement. That is the right place to sit: the evidence
supports damping a self-report, not overriding it. Had the blunt version
shipped, this backtest would be an argument to revert it.

**\`MIN_FOR_ADJUSTMENT = 5\` is too low to act on, even with shrinkage.**
Directional accuracy in these runs reads 0.511 / 0.580 / 0.640 for true
IC of 0 / 0.2 / 0.4. Separating those requires on the order of 100
resolved predictions; at n = 5 the standard error on a hit rate is ±22
percentage points, which spans the entire range the parameter is trying to
distinguish. The K = 20 pseudo-count means a 5-observation user is moved
only 20% of the way, which limits the damage — but the threshold governs
what the *user is told*, and telling someone they are overconfident on
five coin flips is the failure mode \`describe()\` should not have. Raise
the actionable threshold, or state the interval alongside the number.

**\`direction_hit\` is drift-contaminated; do not promote it.**
\`resolve_prediction\` defines it as "final > entry", which in a rising
market is right most of the time regardless of skill. In these runs a
*zero-skill* investor measured 0.511-0.513 directional accuracy against a
0.491-0.506 surprise accuracy (forecast versus the equilibrium prior); the
gap is small only because the synthetic drifts are modest. Real bull-market
drift will hand coin-flippers a 60%+ "hit rate". The Brier score already
uses the harder \`target_hit\` event, which is better, but a bullish target
in a rising market is still easier than a bearish one — the drift-free
version scores the forecast against \`Π\` for that asset and horizon, which
the journal has everything it needs to compute.

**Two changes look higher-leverage than any calibration tuning**, and both
fall out of §7:

- Cap or transform the annualized view return before it reaches
  Black-Litterman (§7.3). Convictions implying +1000%/yr are an input
  error, not a signal, and no confidence weighting rescues them. This is
  the single most likely source of a genuinely bad allocation today.
- Treat the 35% position cap as a first-class, documented risk control
  rather than an incidental default (§7.2). It is currently the main thing
  standing between a face-value view and a one-name portfolio, and the
  value of the entire confidence channel is conditional on it. Keying it to
  γ would make that explicit.

**Do not claim calibration improves returns.** On this evidence it does
not: it is a guardrail against a known failure mode (overconfidence,
concentration), worth most to high-γ users, to the demonstrably
overconfident, and to anyone whose book is not otherwise capped. Every
\`calibrated > stated\` figure in §5 rises when the user is 2× overconfident
(0.270 → 0.380, 0.290 → 0.390), and §7.2 shows the effect becomes large
once the position cap stops binding. It also cuts turnover by 45-63% for
low-skill users (§7.4), which is a real saving the frictionless Sharpe
comparison does not credit. Those are the honest claims. "It makes your
portfolio perform better" is not one of them.

---

## Reproducing

\`\`\`bash
python -m pytest tests/test_conviction_backtest.py -q     # ~8s, offline
python research/conviction/run_conviction_backtest.py --investors 40 --workers 4
python research/conviction/analyze.py            # the §3-§6 tables
python research/conviction/sensitivity_dgp.py    # §7.1
python research/conviction/sensitivity_cap.py    # §7.2
\`\`\`

Everything is seeded and runs offline; the parallel runner reproduces a
serial run row for row. \`research/conviction/results/summary_*.csv\` and
\`diagnostics_*.csv\` are the outputs behind every table above (the ~4 MB
per-investor panels are regenerated rather than stored).
`,Vu=`# The behaviour gap

## The assumption every backtest makes

Every backtest in this repository, and almost every backtest anywhere,
silently assumes the investor held the strategy through everything it
did. They did not. Real investors capitulate after drawdowns, sit in cash
while the recovery happens, and return once it feels safe — which is to
say, after the recovery.

The gap between what a strategy returned and what its investors returned
runs to whole percentage points a year. That is not a rounding error
against the differences most of finance argues about, and it is invisible
to every other number on Hone's evidence page.

It is also the strongest argument for the product existing, which is
exactly why it deserves to be measured rather than asserted. If a
portfolio matched to someone's measured risk tolerance is one they are
more likely to keep holding, the γ-matched book should lose less to
capitulation than an aggressive one — **even where the aggressive one
wins on paper**.

## The panic rule

The threshold is not a free parameter. The Merton rule puts
α* = (μ − r)/(γσ_m²) of wealth in the risky asset; pricing the market at
a Sharpe ratio S — so the premium is S·σ_m, the same assumption
\`calibrate_delta\` makes when building the equilibrium prior — collapses
it:

\`\`\`
σ_target = α*·σ_m = S / γ
\`\`\`

The market's volatility cancels, and so does its realized return. The
drawdown at which someone capitulates is then the 95% one-year VaR of
that budget, \`1.645·σ_target\`, bounded to [8%, 60%].

| γ | Tier | Sells after a drawdown of |
|---|---|---|
| 0.5 | risk-seeking | 60% (the cap) |
| 1.2 | mildly averse | 55% |
| 2.5 | risk-averse | 26% |
| 5.0 | very averse | 13% |
| 8.0 | extremely averse | 8% (the floor) |

**Two earlier versions of this used sample estimates and both broke.**
A per-strategy premium made tolerance a function of the *strategy's*
Sharpe ratio, so the same person tolerated a 60% drawdown in a bad fund
and 8% in a good one. A market-wide sample premium was negative over the
demo window, which pinned every γ to the same cap. A capitulation point
is a property of the person; it should not move because five years of
history happened to be poor.

## The two details that carry the model

**Drawdown is measured against the realized peak**, not the paper one.
Someone who sold and re-entered lower measures their pain from where
their own account peaked. Re-entering resets that peak — an investor who
capitulated and bought back has, in the only sense that matters here,
accepted the loss. Without the reset the simulation re-panics on the next
bar and parks the investor in cash permanently, an artifact of
bookkeeping rather than of anyone's psychology.

**Re-entry waits for confirmation.** The market must climb 10% off its
low since the sale before it feels safe again. This is what makes
capitulation cost anything, because it structurally buys back above the
trough.

A fixed cooldown does not have that property and can be accidentally
well-timed. The first version of this module used one, and produced a
panicking investor who *beat* the strategy by 21 points a year. That is a
stop-loss backtest wearing the wrong label, and it would have been a
flattering, useless result.

Costs are charged: 10bp per switch, and cash earns 4% rather than zero —
the two omissions \`docs/BACKTEST_CONVICTION.md\` flagged in every other
measurement here.

## What it shows

Median behaviour gap across 8 synthetic price panels, γ = 2.5 (sells past
a 26% drawdown). Positive means capitulating cost money:

| Strategy | Median gap | Mean panics |
|---|---|---|
| **Hone (tier-matched)** | **+0.39%** | 0.9 |
| Equal weight | +1.41% | 1.2 |
| 60/40 | +2.38% | 1.5 |
| Buy & hold | +0.05% | 1.8 |
| Performance-chasing | −2.98% | 3.4 |

At γ = 8.0 (sells past 8%) every gap widens to 2–6%, and the ranking of
who suffers least changes with the path.

The tier-matched portfolio has the smallest gap among the diversified
strategies. That is the thesis, and the size of the effect — a few tenths
of a percent at moderate risk aversion, several points at high — is the
credible version of it, not a headline.

## What it does not show

* **Capitulation is not always costly.** On a gentle, straight-line
  decline the trigger fires far above the bottom and selling is a good
  trade. There is a test asserting exactly that, because a simulation
  rigged so panicking always lost would be worthless as evidence. What
  hurts is the drop that overshoots the threshold in a session or two —
  you sell at the low — followed by a rebound that confirmation-waiting
  makes you miss.
* **The rule is a caricature.** Real investors sell partially, sell late,
  sell for reasons unrelated to drawdown, and sometimes never come back.
  One threshold and one re-entry rule is a model of a tendency, not of a
  person.
* **Single paths are noisy.** The endpoint runs one panel, and the
  ranking it reports can flip between paths. The page says so. The table
  above is a median over eight, and eight is not many either.
* **γ is doing double duty.** The same parameter sizes the portfolio and
  sets the panic threshold, so the two are not independent evidence. A
  properly convincing version would elicit loss tolerance separately —
  which is what DOSE could be extended to do.
* **Nothing here is validated against real investor behaviour.** Dalbar
  and Morningstar publish investor-return gaps from actual fund flows;
  this simulation has not been calibrated to them.

## References

* Barber, B. M., & Odean, T. (2000). "Trading is hazardous to your
  wealth." *Journal of Finance* 55(2), 773–806.
* Merton, R. C. (1969). "Lifetime portfolio selection under uncertainty."
  *Review of Economics and Statistics* 51(3), 247–257.
* Kahneman, D., & Tversky, A. (1979). "Prospect theory: an analysis of
  decision under risk." *Econometrica* 47(2), 263–291.
* Benartzi, S., & Thaler, R. H. (1995). "Myopic loss aversion and the
  equity premium puzzle." *QJE* 110(1), 73–92.
`,Wu=`# Linking brokerages

Hone can read your real holdings from every brokerage you use (Schwab,
Fidelity, Robinhood, Interactive Brokers, Webull, E*Trade, Vanguard,
Coinbase and others), combine them into one portfolio, and run every tool on
it. It does this through **[SnapTrade](https://snaptrade.com)**, a brokerage
aggregator: Hone integrates with SnapTrade once, and SnapTrade connects to
the brokers.

**It's off until you configure it.** Without SnapTrade keys, the Data &
account page offers sample data and an Alpaca paper account, exactly as
before.

## What users see

1. **Data & account → Your brokerages → Link a brokerage.**
2. SnapTrade's page opens. They pick a broker and sign in **there**. Hone
   never sees a brokerage password.
3. They come back to Hone. The linked brokerages and their accounts are
   listed, and **Check holdings** shows what was combined, plus every
   position that was left out and why.
4. Every tool (overview, portfolio, hedging, backtest) now uses those
   holdings. Each user can link as many brokerages as they like.

Connections are **read-only**. Hone asks SnapTrade for data access only and
has no code path that places an order.

## Set it up (about 15 minutes)

### 1. Get SnapTrade keys

Sign up at [dashboard.snaptrade.com](https://dashboard.snaptrade.com) and
create API keys. You get a **client ID** and a **consumer key**. The consumer
key signs every request, so treat it like a password.

SnapTrade charges per connected user per month (check their pricing page for
current rates). Users who never finish linking a broker cost nothing.

### 2. Give the server the keys

\`\`\`bash
export SNAPTRADE_CLIENT_ID=...
export SNAPTRADE_CONSUMER_KEY=...
\`\`\`

On Render/Fly, add them as environment variables or secrets. They never
reach the browser.

### 3. Give it a price source

SnapTrade answers "what does this person hold?". Price history, which Hone
needs for risk, still comes from Alpaca market data. Free Alpaca keys work:

\`\`\`bash
export ALPACA_DATA_API_KEY=...       # used ONLY for price history
export ALPACA_DATA_SECRET_KEY=...
\`\`\`

These keys are only ever used to fetch prices, never to read an account, so
they're safe on a public server (unlike \`ALPACA_API_KEY\`, which \`HONE_PUBLIC\`
refuses). On a private server, the regular \`ALPACA_API_KEY\` /
\`ALPACA_SECRET_KEY\` also work. A user who has entered their own Alpaca keys
uses those instead.

### 4. Public servers: turn on sign-in

With \`HONE_PUBLIC=1\` (the Dockerfile default), linking a brokerage requires
signing in with a Hone account. Each link is a paid SnapTrade user, and
tying links to accounts means one person gets one SnapTrade user, and a
stranger can't run up your bill.

Set up Supabase as described in [Accounts & saved portfolios](SUPABASE.md),
**including step 2b**, which creates the \`broker_links\` table. That table is
what lets a user's links follow them to another device.

The server verifies sign-ins against the same Supabase project the browser
uses. By default it reads the URL and key from \`hone/web/static/config.js\`.
Set \`SUPABASE_URL\` / \`SUPABASE_ANON_KEY\` to override.

On a private server (\`HONE_PUBLIC\` unset), sign-in is optional. Without it,
the link lives in that browser only.

## What gets modelled

| Position | Stocks product | Crypto product |
|---|---|---|
| Stocks, ETFs, ADRs, closed-end funds (USD) | ✅ combined across accounts | listed as skipped |
| Crypto | listed as skipped | ✅ (stablecoins count as cash) |
| Cash, money-market sweep | listed as skipped (cash) | listed as skipped |
| Options | listed as skipped (not modelled yet) | listed as skipped |
| Mutual funds | listed as skipped (no daily price feed) | listed as skipped |
| Non-USD listings (e.g. \`VAB.TO\`) | listed as skipped (no FX conversion) | listed as skipped |
| Anything with no price history | listed as skipped | listed as skipped |

The same ticker held at two brokers becomes one holding. Bank, credit and
annuity accounts are ignored. The portfolio value Hone uses for hedge sizing
is the value of what it models. Skipped positions and cash are shown but not
counted.

## How it works

- \`hone/market_data/brokers/snaptrade.py\`: a small signed REST client (no SDK
  dependency) plus \`combine_positions\`, which merges accounts and decides
  what is modelled. Holdings are cached for 60 seconds
  (\`HOLDINGS_CACHE_SECONDS\`), because Hone recalculates often and SnapTrade
  rate-limits some accounts to about 10 requests a minute.
- \`hone/web/app.py\`: \`/api/broker/connect\`, \`/accounts\`, \`/disconnect\` and
  \`/unlink\`, plus a branch in the market loader. When a request carries
  \`credentials.broker\`, holdings come from SnapTrade and prices from Alpaca.
- \`frontend/src/pages/workspace/BrokeragesPanel.jsx\`: the UI.
- A user's SnapTrade identity is a **link**, \`{ user_id, user_secret }\`. It
  is kept in the browser (and in the user's own \`broker_links\` row when
  signed in) and sent with each request, like Alpaca keys. The server stores
  nothing. A link is useless without the server's consumer key, which signs
  every SnapTrade request.

## Troubleshooting

| Message | Meaning |
|---|---|
| *Brokerage linking isn't configured on this server* | \`SNAPTRADE_CLIENT_ID\` / \`SNAPTRADE_CONSUMER_KEY\` aren't set. |
| *Sign in to link your brokerages* | Public server and not signed in. |
| *This server has no price-history source* | Set \`ALPACA_DATA_*\`, or enter Alpaca keys on the page. |
| *Your brokerage link is no longer valid* | The link's secret was rejected. Use **Remove all brokerage links**, then link again. |
| *Already linked from another device* | Sign in with the same account (the link comes with it), or **Reset and relink**. |
| A broker shows **Needs reconnecting** | The broker stopped sharing data, usually after a password change. Press **Reconnect**. |
`,$u=`# The decision journal and confidence calibration

## The problem this solves

Hone measures almost everything it uses. γ comes from an incentivized
Holt-Laury experiment. Σ comes from price history. Π comes from the
user's own holdings. One number is different: **confidence**, which the
user simply types in.

That number is not decorative. In Black-Litterman it drives Ω, the
view-uncertainty matrix, through the Idzorek mapping — it is the single
lever deciding how far the posterior moves from equilibrium. Type 90%
and the optimizer treats your price target as near-fact and concentrates
into it. Type 30% and it barely registers.

And self-reported confidence is, in the literature, the least reliable
number a forecaster produces. Lichtenstein, Fischhoff & Phillips (1982)
established the base finding across domains: people asked for events they
are 90% sure of are right roughly 70–75% of the time, and the gap widens
with difficulty. Barber & Odean (2000, 2001) traced the same
overconfidence directly into retail trading accounts — the most active
traders underperformed the market by ~6.5 percentage points a year, and
the effect was strongest where overconfidence was strongest.

So Hone was, until this module, doing careful measurement everywhere
except at the one input that most determines the answer.

## What it does instead

Every view a user acts on is logged at the moment they commit — the
optimize request that produced their trade list is the same event that
writes the journal entry. The entry freezes the ticker, **the server's
price**, the target, the horizon and the stated confidence. Nothing is
reconstructed afterwards, because a record assembled from memory is a
record of what someone now believes they believed.

When the horizon elapses the prediction resolves against the market:

| Event | Definition | Used for |
|---|---|---|
| \`target_hit\` | Final price at or beyond the target | The Brier score and the calibration fit — it is literally what the confidence claimed |
| \`direction_hit\` | Price simply moved the way the user said | Reported, **never scored** — see below |
| \`touched\` | Target reached at any point before expiry | Shown only. A target touched and given back is not a forecast that paid, but "you were right and didn't take it" is the most useful thing a journal can say |

\`direction_hit\` is shown because "right on direction, too greedy on
magnitude" is a different and fixable problem from "simply wrong". It is
kept out of the score because it is **contaminated by drift**: in a
rising market a coin-flipper who is long by habit clears 60% on it while
knowing nothing. The conviction backtest measured the effect directly — a
zero-skill investor scored 0.511 directional against 0.491 when the same
calls were graded against the equilibrium prior instead of against zero.
Feeding it into the calibration map would hand users a flattering number
manufactured by the market going up.

A prediction whose price data is missing stays **open** rather than being
scored a miss. Counting our data gaps as the user's failures would
quietly manufacture overconfidence.

## Scoring

The Brier score (Brier 1950) is the mean squared error of the stated
probability against the binary outcome. Murphy's (1973) decomposition
splits it into three parts that answer different questions:

\`\`\`
BS = reliability − resolution + uncertainty
\`\`\`

* **Reliability** — does 70% mean 70%? Lower is better; zero is perfect
  calibration.
* **Resolution** — do the calls you're confident about land more often
  than the ones you're not? Higher is better. This is the part that
  cannot be faked by predicting the base rate.
* **Uncertainty** — the variance of the outcomes themselves. A property
  of the questions, not the forecaster.

The distinction drives what Hone does with the score. Poor reliability
with good resolution means the user knows something and states it badly:
rescale their confidence, don't discard it. Zero resolution means the
number carries no information at all, and no rescaling helps.

## The calibration map

A one-parameter-pair logistic regression in log-odds space:

\`\`\`
logit(p_used) = a + b · logit(p_stated)
\`\`\`

fitted by maximum likelihood, with \`a ∈ [−4, 4]\` and \`b ∈ [0, 3]\`. The
bounds matter: under perfect separation — a user whose every call so far
has hit — the unconstrained MLE diverges to infinity.

The fit is then **shrunk toward the identity map** (a = 0, b = 1) by a
pseudo-count of 20 calibrated observations:

\`\`\`
a_used = w · â          b_used = w · b̂ + (1 − w)          w = n / (n + 20)
\`\`\`

Shrinkage is not a nicety, and the threshold below which nothing happens
at all is not either. Both were tested rather than assumed — see
[docs/BACKTEST_CONVICTION.md](BACKTEST_CONVICTION.md), which simulated a
population of investors and compared this design against the two obvious
alternatives:

* Replacing stated confidence **outright** with the realized hit rate —
  the blunt version of this feature — *lost* on the majority of investor
  draws (it won 27-54% in equities, 26-41% in crypto). It helps the
  overconfident and taxes anyone with genuine edge, because a hit rate is
  a slow, noisy estimator that caps confidence near 0.23 even for a good
  forecaster. Shrinking toward the user's own number is what makes the
  feature safe.
* Acting at **five** resolutions, the original threshold, was acting on
  noise: the standard error on a hit rate at n=5 is about ±22 percentage
  points, and separating a forecaster with a real information coefficient
  of 0.2 from one with none takes on the order of a hundred resolutions.
  The threshold is now **25**, which is still optimistic and is the least
  defensible number in this module.

Below the threshold nothing is adjusted at all — the page is a record,
not yet a correction.

Two more guards:

* The adjusted confidence is clipped to [0.05, 0.95]. Black-Litterman
  needs a positive confidence, and a bad run should never erase a user's
  voice entirely.
* The journal records the **stated** confidence, never the adjusted one.
  Scoring our own output would feed the calibration its own tail and
  discount the user a little further on every pass.

## Where it lives

Nothing is stored server-side. The journal lives in the browser under
\`hone-journal:<asset class>\`; \`POST /api/journal\` receives it, resolves
what it can against market data, and returns the verdict plus the fitted
map. The map is cached in page state and sent back with the next
\`POST /api/optimize\`, which applies it server-side so the arithmetic has
exactly one implementation. When a view's confidence is rescaled the
optimize page says so explicitly — the correction is disclosed, never
silent, and can be switched off on the record page.

## Known limitations

* **Selection.** Users journal the views they act on, not the views they
  consider. A user who only acts on their strongest ideas is scored on a
  truncated sample, and the fit is conditional on that.
* **Small n.** Retail users will have tens of resolved predictions, not
  thousands. The reliability curve uses five buckets rather than ten for
  this reason, and it is still noisy. Read the shape, not the wiggles.
* **The evidence for this feature is mixed, and honestly so.** The
  simulation says the confidence channel moves median Sharpe by less than
  0.05 in the shipped configuration, against a 0.16 gap between having
  forecasting skill and not. Confidence handling is a guardrail, not an
  edge — it earns its place by limiting the damage a badly-calibrated user
  does to themselves, not by making anyone money.
* **Horizon clustering.** Predictions made in the same week resolve in
  the same market. Twelve calls made into one drawdown are closer to one
  observation than twelve, and the score does not currently correct for
  this — it will overstate how much evidence a burst of activity provides.
* **The target event is demanding.** Reaching a specific price by a
  specific date is much harder than being directionally right, so hit
  rates look low and almost everyone reads as overconfident. That is why
  the direction-only rate is shown beside it. Users who are consistently
  right on direction and short on magnitude have a fixable problem, and
  the page should tell them which one they have.

## References

* Brier, G. W. (1950). "Verification of forecasts expressed in terms of
  probability." *Monthly Weather Review* 78(1), 1–3.
* Murphy, A. H. (1973). "A new vector partition of the probability
  score." *Journal of Applied Meteorology* 12(4), 595–600.
* Lichtenstein, S., Fischhoff, B., & Phillips, L. D. (1982). "Calibration
  of probabilities: the state of the art to 1980." In *Judgment Under
  Uncertainty: Heuristics and Biases*.
* Barber, B. M., & Odean, T. (2000). "Trading is hazardous to your
  wealth." *Journal of Finance* 55(2), 773–806.
* Barber, B. M., & Odean, T. (2001). "Boys will be boys: gender,
  overconfidence, and common stock investment." *QJE* 116(1), 261–292.
* Idzorek, T. (2007). "A step-by-step guide to the Black-Litterman
  model." In *Forecasting Expected Returns in the Financial Markets*.
`,Ku=`# Hone Crypto — research basis and parameter choices

Hone Crypto applies the **same protocol** as the equities product to
digital assets: Holt-Laury multiple price list → CRRA maximum likelihood
with Fechner noise → 50 tiers → Ledoit-Wolf shrinkage covariance →
Black-Litterman with Idzorek confidence → γ-aware mean-variance
optimization → Merton risk budget → hedge sizing.

This document records the literature that supports reusing that protocol,
the places where crypto's statistical character strains it, and every
parameter that differs (and why).

---

## 1. Does mean-variance + Black-Litterman transfer to crypto?

The literature says yes — with the important caveat that estimation error
dominates, which is precisely the problem Black-Litterman and shrinkage
exist to solve.

- **Platanakis & Urquhart, "Portfolio management with cryptocurrencies:
  The role of estimation risk"** (*Economics Letters*, 2019) is the
  closest paper to what Hone does. It compares naïve 1/N diversification,
  plain Markowitz, and Black-Litterman with variance-based constraints on
  crypto portfolios, and finds **Black-Litterman with constraints
  delivers superior out-of-sample risk-adjusted returns and lower risk**.
  Their conclusion — that raw Markowitz on crypto is wrecked by
  estimation error, and that a Bayesian equilibrium anchor fixes it — is
  the core justification for keeping our exact pipeline rather than
  simplifying it for crypto.
  ([SSRN](https://www.ssrn.com/abstract=3287176) ·
  [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0165176519300254) ·
  [preprint PDF](https://centaur.reading.ac.uk/81734/1/ELs-Blind.Submission.R&R%5B1%5D.pdf))
- Black-Litterman-optimized crypto portfolios are reported to **bear less
  risk, hold more diversity across assets, and produce fewer extreme
  allocations** than unconstrained mean-variance — the same argument for
  the equilibrium prior we already use.
- Recent work extends MVO on crypto with additional signals (e.g.
  **sentiment-aware MVO**, arXiv 2025), confirming MVO as the standard
  backbone researchers build on rather than discard.
  ([arXiv:2508.16378](https://arxiv.org/pdf/2508.16378))
- **"Simple and Effective Portfolio Construction with Crypto Assets"**
  ([arXiv:2412.02654](https://arxiv.org/html/2412.02654v1)) and
  ([arXiv:2511.13239](https://arxiv.org/pdf/2511.13239)) treat
  risk-managed allocation — rather than directional speculation — as the
  serious approach to the asset class.

**Honest caveat, stated in the same literature:** the Gaussian-returns
and constant-covariance assumptions underpinning MVO "are often violated
in cryptocurrency markets, where returns have heavy tails and abrupt
regime shifts." We therefore keep the protocol but **do not** rely on
volatility alone to communicate risk — see §4.

## 2. Is CRRA risk elicitation valid for crypto investors?

The measurement instrument needs no change, and this is well supported:

- Switching points in a multiple price list are **a validated proxy for
  risk aversion under expected utility theory, mapping directly to CRRA
  parameters**; CRRA is "extensively used in experimental and applied
  economics due to its tractability, empirical plausibility, and
  alignment with expected utility theory when evaluating risky choices
  involving proportional or multiplicative changes in wealth."
  Proportional/multiplicative wealth changes describe crypto exactly.
- Crypto investor risk preferences are **heterogeneous and
  time-varying**, and Bitcoin is the dominant transmitter of risk-aversion
  spillovers across the asset class — supporting both (a) measuring each
  individual rather than assuming a "crypto investor" archetype, and
  (b) using BTC as the market/risk proxy.
  ([Annals of Operations Research, 2024](https://link.springer.com/article/10.1007/s10479-024-06001-9))
- Retail crypto risk perception clusters around "the possibility of
  losing money," "volatility and uncertainty," and "limiting investment
  to affordable amounts" — which is why the product expresses the risk
  budget in **dollars of drawdown** rather than in σ.
  ([ScienceDirect](https://www.sciencedirect.com/science/article/pii/S2214635024001096) ·
  [Journal of Asset Management](https://link.springer.com/article/10.1057/s41260-022-00302-z))

**Conclusion:** the questionnaire, the MLE, and the 50 tiers are
**byte-for-byte identical** across both products. A test asserts this
(\`test_questionnaire_protocol_is_unchanged\`).

## 3. Covariance estimation under heavy tails

- Shrinkage remains the right default. Work on **covariance estimation
  for minimum-variance portfolios under heavy tails** confirms shrinkage
  estimators are the practical choice, while cautioning that estimators
  tuned for *accuracy* are not always optimal for *portfolio variance*.
  ([arXiv:2606.27462](https://arxiv.org/html/2606.27462v1))
- Random-matrix-plus-shrinkage hybrids improve the bias-variance
  trade-off under heavy-tailed data
  ([arXiv:1912.03718](https://arxiv.org/pdf/1912.03718)) — a natural
  future upgrade, not a change needed for parity.
- Crypto **tail-risk is strongly interconnected**: tail dependence
  transmits across coins, and conditional tail risk (CoVaR) is large for
  BTC/ETH/XRP/LTC. This is the quantitative statement of "correlations go
  to 1 when it matters."
  ([LASSO quantile regression](https://sciencedirect.com/science/article/abs/pii/S0927539820300372?via=ihub%3D) ·
  [Conditional tail-risk in cryptocurrency markets](https://ideas.repec.org/a/eee/empfin/v50y2019icp1-19.html))
- Long-memory, asymmetric volatility models with heavy-tailed innovations
  outperform for crypto VaR
  ([Frontiers, 2025](https://www.frontiersin.org/journals/applied-mathematics-and-statistics/articles/10.3389/fams.2025.1567626/full)).

**What we did about it:** kept Ledoit-Wolf shrinkage (same protocol), and
made the *communication* tail-aware — the stress table uses realized
crypto drawdowns (−84%, −77%) instead of model-implied losses, and the UI
states that betas rise and correlations converge in real crashes.

## 4. Hedging: stablecoins first, futures second

- **Stablecoins mitigate downside risk in crypto portfolios.** USDC acted
  as a hedge across a full sample (notably in the first five months of the
  pandemic) while USDT behaved only as a diversifier — i.e. the
  dollar-pegged leg is the reliable risk reducer.
  ([ScienceDirect, 2022](https://www.sciencedirect.com/science/article/pii/S1062940822001735))
- **Perpetual futures** neutralize downside for spot holders without
  selling, with hedge ratios typically 50–100% of exposure — but carry
  **liquidation risk from leverage and persistent funding costs that
  erode hedge effectiveness**.
- BTC futures **require only a minimal allocation** in diversified
  portfolios, and crypto "enhances diversification in normal periods and
  increases volatility during crises" — a caution against treating a
  crypto short as a benign hedge.
  ([Eurasian Economic Review, 2025](https://link.springer.com/article/10.1007/s40822-025-00353-8) ·
  [Bitcoin futures crash risk](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10825442/))
- Simulation frameworks integrating volatility, hedging, contagion and
  Monte Carlo support explicitly modeling contagion for crypto risk
  ([arXiv:2507.08915](https://arxiv.org/pdf/2507.08915)).

**What we did about it:** the hedge set is (1) a **stablecoin
allocation** — exact, no derivatives, no liquidation risk — and (2) a
short of the market proxy, which now emits an explicit **warning whenever
notional exceeds 50%** citing margin, funding and liquidation. Listed
options are omitted because they are not available via the brokerage
integration.

---

## 5. Parameter differences (and only these)

| Parameter | Equities | Crypto | Why |
|---|---|---|---|
| Periods per year | 252 | **365** | Crypto trades continuously; annualization only. |
| Market proxy | SPY | **BTC/USD** | BTC is the dominant risk factor and the documented transmitter of risk-aversion spillovers. |
| Stress scenarios | 2008 −55%, 2020 −34%, 2022 −25% | **2018 −84%, 2022 (Terra/FTX) −77%, May 2021 −53%, Mar 2020 −50%** | Realized peak-to-trough BTC drawdowns. |
| Cash leg | Cash / T-bills | **USDC or another dollar stablecoin** | Crypto-native risk-free-ish leg (see §4). |
| Options overlay | Available (live Alpaca chains) | **Disabled** | No listed crypto options through the integration. |
| Data endpoint | \`/v2/stocks/bars\` | \`/v1beta3/crypto/us/bars\` | Alpaca crypto data needs no market-data subscription. |
| Questionnaire, MLE, tiers, shrinkage, BL, MVO, Merton budget | — | **identical** | §1–§2. |

## 6. One protocol change that crypto forced — and it improved equities too

Applying the pipeline unchanged surfaced a genuine bug in the *original*
equities implementation. Reverse optimization used the **investor's own
γ** as the market's risk aversion δ:

\`\`\`
Π = δ Σ w,  with δ = max(γ, 0.5)
\`\`\`

Because Π scales with variance, crypto's ~15× larger variances produced
equilibrium returns near **+100%/yr**, so a genuinely bullish +50%/yr
view registered as *bearish* and the optimizer sold the asset the user
liked. Textbook Black-Litterman calibrates δ to the **market**, not the
individual. We now set

\`\`\`
δ = S / σ_m,   S = 0.40 (target market Sharpe)
\`\`\`

which yields δ ≈ 2.5 at σ_m ≈ 16% (the canonical equity value) and
δ ≈ 0.67 at σ_m ≈ 60%. This is applied identically in both products, so
protocol parity is preserved and the equities priors became more
principled as a side effect. See \`calibrate_delta\` in
\`hone/optimization/black_litterman.py\`.

## 7. Known limitations

1. **Volatility-based risk budgets understate crypto crash risk.** The
   Merton budget assumes σ summarizes risk; crypto's tails mean an 80%
   drawdown is not a 5σ event. The dollar stress table exists to
   compensate, but a CVaR/drawdown-based budget is the principled
   upgrade (tracked in \`docs/ROADMAP.md\`).
2. **Beta-approximated crash losses are optimistic** — betas rise and
   correlations converge exactly when it hurts. The UI now says so.
3. **A low-γ user can be told a 68%-volatility portfolio needs no hedge.**
   That is the identical protocol behaving correctly, and it is
   defensible for a measured risk-seeker — but it is the strongest
   argument for adding a fat-tail-aware floor.
4. **Demo mode is synthetic** (Student-t, df=4, ~55–110% vols, ρ≈0.75).
   Calibrated to look like crypto, but it is not history. Backtest
   conclusions require the live data path.
5. **No on-chain, staking, or self-custody risk** is modeled: no
   depegging, bridge failure, exchange insolvency, or smart-contract
   risk. These are real crypto risks that a covariance matrix cannot see.
`,Gu=`# Flexible views: entropy pooling

## The throat in Black-Litterman

Black-Litterman is a good engine with a narrow throat. A view has to be a
**linear statement about expected returns** under a **joint normal**
distribution: *NVDA returns 18%*. That is one shape of belief, and it is
not the shape most beliefs have.

Things a user can hold and the main flow cannot accept:

* "There's a one-in-three chance Tesla drops more than 20% this year."
* "I don't know where Nvidia lands, but I'm confident it beats Intel."
* "If Bitcoin falls 20%, Ethereum falls at least as far."
* "Volatility is going to be higher than the last two years suggest."

The first and fourth are statements about the *shape* of the
distribution, not its centre. The second has no number in it at all. The
third is a conditional relationship that a full-sample covariance matrix
averages away — it is precisely the correlation everyone discovers during
the crash and not before.

Forcing these through a price-target box means asking the user to invent
numbers they do not have, which is the single worst thing a tool like
this can do: an invented number is indistinguishable from a real one by
the time it reaches the optimizer.

## Meucci's answer

*Fully Flexible Views: Theory and Practice* (Meucci, 2008): stop
parameterizing the distribution. Represent the market as **scenarios with
probabilities**, treat each view as a **constraint on those
probabilities**, and find the posterior that satisfies the constraints
while staying as close to the prior as possible:

\`\`\`
minimize   Σ p̃ᵢ ln(p̃ᵢ / pᵢ)              (relative entropy, Kullback-Leibler)
subject to Ã p̃ = b   (or ≤ b)
           Σ p̃ = 1,  p̃ ≥ 0
\`\`\`

Minimum relative entropy is the right notion of "least distortion": it is
the update that adds **no information beyond what the views assert**.
That is exactly the discipline you want when the views come from a human
who is confident about one thing and silent about everything else.

Every view type reduces to one row: a vector \`g\` over scenarios and a
target for \`E[g]\`.

| View | \`g\` | Says |
|---|---|---|
| Mean | the asset's returns | \`E[r] = q\` |
| Probability | a 0/1 indicator | \`P(r ≤ t) = q\` |
| Ranking | \`r_loser − r_winner\` | \`E[·] ≤ 0\` |
| Volatility | \`r²\` | second moment pinned |
| Conditional | \`1{cond}·(r − q)\` | \`E[r \\| cond] = q\`, kept linear |

## The dual

The primal has one variable per scenario — hundreds or thousands. The
dual has one per view:

\`\`\`
D(λ) = ln( Σᵢ pᵢ exp(−(Ãᵀλ)ᵢ) ) + λᵀb
\`\`\`

minimized over λ, free for equalities and non-negative for inequalities.
The posterior is \`p̃ᵢ ∝ pᵢ exp(−(Ãᵀλ)ᵢ)\` — an exponential tilt of the
prior, the same object that appears in importance sampling and
large-deviations theory, for the same reason. Solved with L-BFGS-B and an
analytic gradient; the log-sum-exp form is not cosmetic, since the tilt
exponent is unbounded in λ and overflows long before convergence.

## What it costs, and saying so

Views are not free. Insisting that a 6%-likely event is 33% likely means
reweighting the scenarios that contain it, and there are only so many.
\`effective_number_of_scenarios\` is \`exp(entropy)\` — Meucci's diagnostic
and the honest answer to *were my views too strong?*

A uniform prior over 700 scenarios has an effective size of 700. If three
views drop that to 90, the posterior is carried by ~90 paths and every
statistic computed from it — the tail above all — is that thin. The page
shows the fraction kept, and flags a collapse rather than quietly
returning a confident-looking number built on nothing.

Measured behaviour on the demo universe:

| View | Effective scenarios kept |
|---|---|
| \`E[TSLA] = +3%\` (prior +0.8%) | 98% |
| \`P(BTC ≤ −15%) = 30%\` | 79% |
| \`E[ETH \\| BTC ≤ −20%] = −30%\` | 95% |
| \`P(TSLA ≤ −25%) = 60%\` | collapses — flagged |

## Why this fits the rest of Hone

The posterior is a **reweighted set of the same scenarios**, and
\`hone/optimization/cvar.py\` already optimizes over scenarios. Chaining
them gives a path from belief to portfolio that assumes normality
*nowhere*:

\`\`\`
empirical scenarios → entropy-pooled posterior → CVaR optimization
\`\`\`

Black-Litterman remains the default route: it is what the confidence
calibration in \`hone/journal/\` is fitted against, and what the hedging
engine's γ→volatility budget is built on. This is the route for views the
default cannot represent.

## Known limitations

* **Nothing here is calibrated.** The decision journal scores price-target
  views because they resolve unambiguously. "I think A beats B" also
  resolves, but is not yet logged; probability views are far harder,
  since a single outcome barely tests a stated probability.
* **Views can be mutually impossible.** Two constraints the scenario set
  cannot satisfy together drive the effective sample toward zero rather
  than failing loudly. The collapse warning is the signal; there is no
  infeasibility certificate.
* **Resampling to feed the CVaR optimizer adds noise.** The optimizer
  treats rows as equally likely, so a weighted posterior is resampled
  before use — sampling error on top of an already-thin tail. Passing
  probabilities through directly would be better and is not done yet.
* **History bounds imagination.** A view about an event with no instance
  in the price history cannot be expressed at all: there are no scenarios
  to reweight. This is a real ceiling, and the reason the conditional
  view refuses to condition on fewer than five scenarios rather than
  returning an average of two.

## References

* Meucci, A. (2008). "Fully Flexible Views: Theory and Practice."
  *Risk* 21(10), 97–102.
* Meucci, A. (2010). "Historical Scenarios with Fully Flexible
  Probabilities." *GARP Risk Professional*.
* Kullback, S., & Leibler, R. A. (1951). "On information and
  sufficiency." *Annals of Mathematical Statistics* 22(1), 79–86.
* Cover, T. M., & Thomas, J. A. (2006). *Elements of Information
  Theory*, ch. 11 (information geometry and exponential tilting).
`,Yu=`# The income-hedge model, in one page

This is the complete specification of how Hone sizes an income hedge. The
code is in \`hone/prediction/hedge.py\`; every rule below names the constant
that controls it and the study that justified it. The studies are in
\`research/prediction/findings/\`:

| File | What it did |
|---|---|
| 01_research.md | Kalshi rules, index-insurance literature, alternatives |
| 02_history.md | Backtest on 2,822 settled Kalshi markets |
| 03_segments.md | 78,480 simulated people across 8 occupations |
| 04_properties.md | Adversarial property tests (found 14 engine bugs) |
| 05_misspecification.md | What happens when the model's assumptions are wrong |

## What goes in

| Input | Meaning |
|---|---|
| \`wealth\` | Money available over the season: earnings plus savings. For a business, cash reserves plus a normal season's profit. |
| \`loss\` | Dollars lost in a bad season. |
| \`price\` | What the protective contract costs (the ask). |
| \`market_prob\` | The market's probability (the midpoint). Kalshi prices are well calibrated (02: Brier 0.109, slope 1.01), so this is trusted. |
| \`own_prob\`, \`confidence\` | Optional: your own view, and how sure you are. |
| \`basis_correlation\` | How closely the contract tracks *your* loss, from 0 to 1. |
| \`loss_prob\` | Optional: your own chance of a bad outcome, when it differs from the contract's event. For example, a layoff is rarer than "unemployment above 4.5%". |
| \`gamma\` | Your risk aversion, from Hone's questionnaire. |
| \`liquidity\` | Open interest and the order book (looked up by ticker). |

## How the size is chosen

1. **Insurance at the market's odds.** Hone finds the position that maximizes
   your expected CRRA utility if the market price is the true probability.
   That position is the hedge.
2. **Your view, capped.** If you gave a view, Hone also finds the position
   that is best at your own probability. The difference from step 1 is a bet
   on your view, so for anyone with income at risk it is limited to
   \`MAX_VIEW_TILT\` = **0.25×** the insurance part.
   - **Why:** views were 2 to 8 times the insurance part, and an overconfident
     user could lose up to 107% of income (03, 05).
   - **Cost:** at 0.25 you keep about 48% of the view's value when it is
     right, against 50% with no tighter limit.
3. **No selling for hedgers.** Someone with income at risk is never told to
   sell their protection (\`allow_selling\` = automatic).
   - **Why:** half of optimists were told to sell (03). At real prices, the old
     wiring told drivers and retirees to sell, and some were wiped out (02).
4. **What the market can supply.** The order book is walked contract by
   contract, at what each contract really costs. The position is capped at
   the smaller of two limits:
   - the depth within \`max_slippage\` (3¢) of the best price;
   - \`DEFAULT_MAX_SHARE_OF_OI\` (**25%**) of open interest.

   The sweep (03) found that 10% gave up most of the value in thin markets
   and left deep markets unaffected.
5. **Safety margins, for choosing the size only.** The size is chosen as if:
   - the contract tracked you \`BASIS_SHRINK\` = **0.75×** as closely as stated
     (people overestimate this);
   - every contract cost \`PRICE_BUFFER\` = **1¢** more (slippage, stale
     quotes, market bias).

   Every dollar figure shown still uses the real price and your stated
   inputs.
   - **Why:** the share of people hurt by a wrong model fell from 24% to 10%,
     and the average harm fell about 4×, for about 19% less value when the
     model is exactly right (05).
6. **Not worth it.** If the best position is worth less than
   \`max(MIN_WORTH_DOLLARS, MIN_WORTH_FRAC × wealth)\` ($5 or 0.05%), Hone
   proposes nothing and says why. 12.5% of the old positions were worth
   under $1 (03).
7. **Whole contracts.** The size is rounded to whichever neighbouring whole
   number is worth more (fees round to the cent), and it stays solvent in
   every outcome that can actually happen.

The optimum is found by solving the first-order condition, where one more
contract adds zero value, by bisection. This is exact. Searching the utility
itself was not exact, because it is flat to 16 digits on large portfolios
(04).

## What comes out

For each plan Hone reports:
- **The proposed position** (contracts, direction, cost, fee, and the average
  fill price).
- **The ideal size** before liquidity limits, and **coverage**, the share of
  the ideal that the market can supply.
- **Insurance part and view part**, plus a reference size: one contract per
  dollar at risk, scaled by basis.
- **Value to you:** the certainty-equivalent gain, the most worth paying per
  contract, and the worst outcome and typical swing with and without the
  hedge.
- **A plain-English warning for every rule that changed the answer.**

## What the evidence says about who it helps

- **Deep markets only.** Inflation and gas markets can supply a meaningful
  share of one person's hedge. Unemployment markets supply about 11%. Most
  others supply 0–2%.
- **Big exposure relative to savings.** For a typical driver ($4.5k at risk
  on $56k), insurance is worth about $26 a year. Kalshi's fee eats most of
  that, so Hone proposes nothing. A full-time driver with no savings and
  $9k at risk gains about $700.
- **Tracking matters more than anything.** Measured upper bounds (02):
  - gas vs. a driver's fuel costs: 0.52–0.68;
  - CPI vs. a retiree's purchasing power: about 0.8;
  - national unemployment vs. one person's job: **0.02**.

  The page's defaults now use these numbers. Labor-market contracts can't
  hedge an individual's job.
- **Basis risk makes demand hump-shaped.** The most risk-averse people buy
  *less* index insurance, because a bad season without a payout gets worse
  with every dollar of premium (Clarke 2016). The engine reproduces this and
  explains it to the user.
- **Protection has been expensive.** Buying the protective side at the ask
  lost 7–19¢ per contract historically (02). That is the insurance premium.

Across the 78,480 simulated people, the effect of these rules (03, rerun):

| | Before | Now |
|---|---|---|
| Crashes | 32 | 0 |
| Told to sell protection they need | 10.5% | 0% |
| Trades worth under $1 | 14.8% | 0% |
| With a view, hurt if the market was right | 46.4% | 4.7% |
| With a view, worst outcome | −133% of income | −0.05% of income |
| Gain more than 0.5% of income | 14.6% | 9.8% |
| Proposed nothing | 24% | 79% |

## Known limits

- **One period, one binary event.** Continuous losses would be better
  served by ladders of strikes (02).
- **Liquidity is a snapshot.** Open interest 28 days before close is 5–20×
  thinner than a week before (02).
- **The safety margins are a policy choice,** tuned on simulated people.
  Change the constants, then rerun \`research/prediction/sweeps.py\` and
  \`research/prediction/misspecification.py\` to see the trade-off.
- **Hone sizes and explains; it never trades.** Selling a payout to a
  customer is insurance or a swap, and both are regulated (01).

## The scenario suite

\`tests/test_hedge_scenarios.py\` writes each lesson above as a person
(a driver, a ski instructor, a contract worker, an optimist, someone
risk-seeking) together with what the model must do for them. Any change to
the engine has to keep passing it. To teach the model something new, add a
scenario that names the person, states the expected behaviour, and cites
the study it came from.


## Pricing protection directly ("Price my risk")

\`hone/prediction/quote.py\` prices protection from a minimal description:
business type, place and revenue. \`hone/prediction/perils.py\` defines what
it can price:

| Peril | Measured | Bad when | Businesses |
|---|---|---|---|
| snow | snowfall Nov–Apr (or peak snow water) | too little | ski resorts, instructors, mountain shops, snow removal |
| rain_summer | rainy days, May–Sep | too many | outdoor venues and events |
| rain_work | days with 5+ mm of rain, Mar–Nov | too many | construction, landscaping |
| heat | days over 32°C, Jun–Aug | too many | outdoor workers |
| cool_summer | days over 30°C, Jun–Aug | too few | HVAC contractors |
| spring_frost | nights ≤ −2°C, Apr–May | too many | orchards |
| drought | rainfall, May–Aug | too little | crop farms |

History comes from the best source available, in this order:

1. A USDA SNOTEL station on the mountain (snow only, western US).
2. The nearest NOAA station with a long and *current* record of that
   measurement. Some stations are "active" while one of their measurements
   stopped years ago; those are skipped.
3. The ERA5 grid, which is available everywhere.

A 30-resort study (findings/07) found that the grid and on-site stations
often disagree about which seasons were bad, so stations win whenever they
exist. The snow sensitivities are measured from Vail's filings
(findings/06). The non-snow sensitivities are still assumptions until
findings/09 measures them, and the quotes say so.
`,Qu=`# Hone Markets — hedging cyclical income with event contracts
> **The current model, every rule and the evidence for it: [HEDGE_MODEL.md](HEDGE_MODEL.md).**


The stocks and crypto products answer one question: *given how much risk you
can carry, how much of this risky asset should you hold?* This product
answers the mirror image for people whose **paycheck is the risky asset**.
A ski instructor's season depends on snowfall; an ad-agency freelancer's
bookings on ad budgets; a recruiter's fees on hiring; a realtor's
commissions on mortgage rates. Each of them holds a position they never
chose, and [Kalshi](https://kalshi.com) — a CFTC-regulated exchange for
event contracts — lists contracts on exactly those events.

This document records the theory the tab runs on, how each piece maps onto
machinery Hone already had, the market catalog and where its data comes
from, and the honest list of what the tool cannot do.

Everything lives in \`hone/prediction/\`; the page is the third product tab
at \`/prediction-markets\`; the API is \`GET /api/predict/markets\` and
\`POST /api/predict/hedge\`.

---

## 1. The problem, in Hone's own terms

Hone measures a person's constant-relative-risk-aversion parameter γ with
an adaptive questionnaire and uses it everywhere downstream through the
utility function

    U(w) = w^(1−γ) / (1−γ)            (γ = 1: U(w) = ln w)

and the **certainty equivalent** CE = U⁻¹(E[U(w)]) — the sure amount worth
the same to this person as an uncertain prospect. The "Certainty equivalent"
tile on the rebalance page is this number for a stock portfolio.

A season of income is a prospect of the same kind. Over the horizon a person
expects wealth W (earnings plus the savings a bad season would eat). If the
bad outcome D happens they lose L. An event contract B pays $1 when the
market's event resolves the way that accompanies the bad outcome; it costs
c per contract plus fees. Buying n contracts leaves

    wealth = W − L·D + n·(B − c) − fee(n, c)

and the person chooses n to maximize E[U(wealth)]. That is the mean-variance
problem of the optimize page with a binary asset in place of stocks. The
code is \`hone/prediction/hedge.py::hedge_income\`; the maximization is exact
(bounded scalar optimization over n, with n kept inside the solvency bounds
that keep wealth positive in every state).

## 2. A price is a probability

A Kalshi contract pays $1.00 on YES and $0 on NO; YES and NO prices sum to
$1. A YES at 35¢ is the market saying 35%. Two frictions are modelled:

* **The spread.** Buyers pay the ask. In thin weather markets the ask can sit
  20–50¢ above the bid (the Northstar snowfall ladder had a 44¢ bid / $1.00
  ask on the day the snapshot was taken). The catalog reports the spread and
  the tool prices at the ask of the side being bought, never the midpoint.
* **The fee.** Kalshi's taker fee is \`ceil_to_cent(0.07 × C × P × (1 − P))\`
  times a per-series multiplier the API reports as \`fee_multiplier\`;
  largest on coin flips, near zero at the extremes. Resting orders are
  generally free. The optimizer uses the smooth (unrounded) fee so the
  objective stays concave, then reports the rounded one. Schedules change;
  the page says the figure is indicative.

\`hone/prediction/contracts.py\` holds \`kalshi_fee\`, \`implied_probability\` (the
midpoint when both sides are quoted, the last trade when the book is empty —
a $0.00 bid / $1.00 ask is not a 50% opinion) and the \`Contract\` type.

## 3. The answer always splits into insurance and a bet

For a small position the CRRA problem is approximately mean-variance.
Writing q for the probability of the bad outcome (after blending, §5) and ρ
for the correlation between the market's event and the person's own loss
(§4), the first-order condition gives

    n* ≈ ρ·L  +  W·(q − c) / (γ·q·(1 − q))

* **ρ·L is the pure hedge** — the position minimizing the variance of
  wealth. It does not depend on price or on γ. It is the exact analogue of
  the beta-sized index short in \`hone/hedging/short_hedge\`: the hedge is
  scaled by how much of the risk the instrument can see, and capped at the
  minimum-variance size.
* **The second term is a bet** on the gap between the person's probability
  and the price, shrunk by γ and by the event's own uncertainty. At a fair
  price with no fees it is zero and *any* risk-averse person hedges the whole
  loss — a result the test suite asserts exactly (\`contracts == L\`,
  \`std_hedged == 0\`). Fees act like a higher price and shrink the hedge; a
  contract the person believes is cheap adds to it.

The page reports the exact optimum and this decomposition side by side, so
a "hedge" that has quietly become a bet is labelled as one. With no exposure
(L = 0) the whole position is the bet, and the result reduces to CRRA bet
sizing: the Kelly fraction (q − c)/(1 − c) at γ = 1, and roughly Kelly/γ
above it — which is where "half Kelly" comes from.

## 4. Basis risk

The contract resolves on a weather station or a government statistic; the
income depends on visitors and bookings. The tool asks for the correlation
ρ ∈ [0, 1] between the two and builds the joint distribution of (contract
pays, income lost) from the shared marginal q and ρ:

    P(both) = q² + ρ·q(1 − q)

ρ is clipped into the Fréchet-feasible range and the value used is reported.
Negative ρ is excluded on purpose: the user picks the contract side so that it
pays when they lose, and a side that paid when they won is not a hedge. The
residual variance (1 − ρ²) of the original stays with the person whatever they
buy, which is why the catalog labels every market **direct**, **close** or
**proxy**, and why the worked example on the concepts page shows the same
exposure at ρ = 0.9 and ρ = 0.6.

How to estimate ρ honestly: count past bad seasons in which the market's number
also came in bad. Every year it did not is a year the hedge would have paid
nothing while income fell anyway.

## 5. The user's view against the market

The market price aggregates everyone else's information. A user who thinks
the odds differ is not taken at their word: the belief is blended the
Black-Litterman way,

    q* = (1 − κ)·p_market + κ·q_user

with the market price as the equilibrium prior, the user's probability as the
view and their confidence κ ∈ [0, 1] as the weight — Idzorek's reading, in
which 100% confidence adopts the view outright. The result is clipped to
[0.01, 0.99] so no certainty can let the optimizer bet everything. A blended
probability more than 15 points from the price triggers a warning.

Prediction markets are the one place a stated confidence can be *scored*: a
probability that resolves YES or NO is exactly what a Brier score measures,
which is the currency of Hone's decision journal (\`docs/CALIBRATION.md\`).
When the journal's calibration map is actionable the \`/api/predict/hedge\`
endpoint applies it to κ before blending, using the same \`apply_calibration\`
as the views page, and the result discloses both the stated and the used
confidence.

## 6. What the hedge is worth, and the most to pay for it

Two numbers turn the position into a decision:

* **Certainty-equivalent gain** CE(n*) − CE(0): the dollar value of the
  insurance to this person. Higher γ values it more; a risk-neutral person
  values it at zero.
* **The reservation price** — the most the person should pay per contract —
  has a closed form. At the price where the first contract is exactly worth
  buying, the marginal condition E[U′(W₀)(B − c)] = 0 gives

      c_max = E[U′(W₀)·B] / E[U′(W₀)]        with U′(w) = w^(−γ)

  the person's probability of the event re-weighted by how much a dollar is
  worth in each state. For the worked example (W = $38,000, L = $9,000,
  q = 35%, γ = 1.5) it is 45¢ against a fair 35¢: the 10¢ gap is the
  insurance premium this person's risk aversion will rationally pay. Above
  c_max the tool shows no position. At γ = 0 it collapses to q.

This is the Merton risk budget of the hedge page written for a binary event:
how much expected return the person's γ gives up to remove risk.

## 7. Where each piece already lived in Hone

| Here | Elsewhere in Hone |
|---|---|
| Risk number γ, 50 tiers | \`hone/risk_profile\` — the same questionnaire, shared across tabs; a γ measured on the Stocks tab is offered on this one |
| Certainty-equivalent gain | The "Certainty equivalent" tile on the rebalance page (\`hone/optimization/mvo.py\`) |
| Pure hedge ρ·L | The beta-sized index short (\`hone/hedging/hedge.py::short_hedge\`, \`portfolio_beta\`) |
| Reservation price c_max | The Merton risk budget (\`gamma_target_volatility\`) |
| Blending odds with the price | Black-Litterman + Idzorek (\`hone/optimization/black_litterman.py\`) |
| Confidence corrected by the record | The journal's Brier scoring and calibration map (\`hone/journal/calibration.py\`) |
| Season with/without the hedge | The stress table on the hedge page |

## 8. The market catalog and its data

\`hone/prediction/kalshi_client.py::INDUSTRIES\` is the curated list: 41 series
in six groups — snow and the ski season (Aspen monthly snowfall, Vail Resorts
skier visits, Colorado and Tahoe resort opening dates, Northstar season
snowfall, New Hampshire and Utah skier visits), advertising and media
(monthly ad-spend indices by category, Super Bowl advertisers), hiring and
layoffs (unemployment, payrolls, weekly claims, holiday retail hiring, tech
layoffs), housing and rates, travel and hospitality (Orlando room nights,
Florida visitors, cruise and hotel KPIs), and fuel and the cost of living.
Each entry carries a basis verdict and the side a hedger buys.

Data comes from Kalshi's public REST API (\`/trade-api/v2/markets?series_ticker=…\`,
no account needed). The server returns at once with the bundled
\`kalshi_snapshot.json\` and refreshes from the live API in a background thread,
caching for ten minutes; \`source\` in the response says which you got.
\`HONE_KALSHI_LIVE=0\` disables live fetching. The snapshot was generated with
\`research/prediction/fetch_kalshi_snapshot.py\` on 3 November 2026 and should
be refreshed when a new season's contracts list (Aspen's December 2026 series
existed but had no open contracts that day).

Hone holds no Kalshi credentials and places no orders. It reads prices, sizes
a position and explains it.

## 9. What this cannot do

* **Remove basis risk.** A proxy hedge leaves the uncorrelated part of the
  season untouched, and even a direct hedge resolves on a measurement rather
  than on a bank balance.
* **See the order book you will trade in.** Thin markets may not fill at the
  ask; Kalshi imposes per-market position limits; fee schedules change.
  Volume and spread are shown so the user can judge.
* **Model more than one period and one binary event.** A real season has many
  months and many thresholds, and the contract settles on its own date, not
  when the income arrives. Laddering several strikes is a natural extension;
  the tool sizes one at a time.
* **Beat the market.** Prediction-market prices are hard to beat. The blend
  and the warnings exist to keep a hedge from turning into an unexamined bet,
  not to encourage one. A gamma at or below zero (risk-neutral or
  risk-seeking) has no interior optimum; the tool then shows the pure hedge
  and says plainly that those preferences do not want insurance.
* **Give advice.** Tax treatment of event contracts, state-by-state
  availability and the legal status of some contract types are the user's to
  check.

## 10. Next steps

* Log sized hedges in the decision journal as probability predictions, so the
  journal's Brier score covers them and the calibration map learns from them
  — the journal's record type is price-target-shaped today.
* Ladder several strikes of one series and size them jointly.
* Multi-period exposures (a whole season of monthly contracts) with the
  horizon-weighted wealth the stocks product already uses.
`,Xu=`# Tuning a model on your own convictions

## The ask, and the arithmetic

The ambition is real and it is a good one: a model tuned on *your*
convictions and how they actually turned out should compile your theses
the way you mean them and price your confidence the way your history
earns. Nobody else's data can teach it your habits.

The arithmetic is less romantic. A retail investor with a year of active
use has perhaps thirty resolved predictions. **Thirty examples is not a
fine-tuning dataset; it is a prompt.** A LoRA trained on thirty rows
memorizes them, and a model that has memorized your last thirty calls is
worse than the base model on the thirty-first — confidently, and in your
own voice, which is the worst possible failure mode for a tool whose job
is to check your reasoning.

So Hone ships two things and is explicit about which is which.

## What works today: in-context personalization

\`hone/llm/personalize.py\`. Your resolved predictions go into the
compiler's system prompt:

* **Style examples** — theses paired with the structured views you edited
  them into, and whether they hit. These teach the model the corrections
  you keep making: that you always mean six months by "medium term", that
  "I like it here" is 55% and not 75%.
* **A calibration note** — one sentence stating your realized hit rate
  against your average stated confidence. This is the sentence that stops
  the model repeating your overconfidence back at you.

Examples are **outcome-balanced**, not just recent: showing only hits
would teach the model you are always right, and showing only the last ten
hands it whatever streak you happen to be on.

No GPU. No training run. Active from **five** resolved predictions, and
better every time one resolves. It also degrades gracefully — a bad
example set makes the model slightly worse, where a bad fine-tune makes
it confidently and permanently worse.

The views page shows \`tuned to your last N\` when it is active.

## What needs more data: QLoRA

\`hone/llm/export.py\` builds two datasets from resolved predictions:

| Dataset | Input | Label | Teaches |
|---|---|---|---|
| \`compile\` | your thesis text | the structured view **you edited it into** | your conventions and the corrections you keep making |
| \`calibrate\` | thesis + the move it implies | **whether it actually hit** | what your language is worth, not what you claim for it |

The second label choice is the important one. Training on *stated*
confidence teaches a model to imitate your overconfidence. Training on
outcomes teaches it what your language actually predicts — the only
version worth having.

Only **resolved** predictions are used. An open prediction has no label,
and training on its stated confidence would teach the model your priors
rather than your accuracy.

The split is **chronological**, never random. A journal is a time series;
a random split puts the same market regime on both sides, so validation
loss flatters the model and answers nothing. The only question worth
asking is whether it helps on the *next* thesis.

### Running it

\`\`\`bash
pip install torch transformers peft bitsandbytes trl datasets accelerate
python training/train_qlora.py --data hone-training.jsonl --out ./adapter
\`\`\`

QLoRA (Dettmers et al., 2023): the base model loads in 4-bit NF4 with
double quantization and stays frozen; only small low-rank adapters train.
That is what puts a 7B model on a single 16GB card. Rank defaults to 8 —
low on purpose, because the task is narrow and a high rank on a small
dataset is a faster route to memorizing it.

The script **refuses to run** below 200 examples unless you pass
\`--force\`, and prints why.

### It does not tune Claude

Claude is not fine-tunable through the public API. The adapter this
produces is a **local open-weights model** that has learned your
conventions and can run offline — a different and complementary thing.
The personalization that reaches Claude is the in-context path above.

The app says this on the export panel, because the assumption otherwise
is natural and wrong.

## Verdicts the export gives you

| Examples | Verdict | What it means |
|---|---|---|
| < 200 | \`few_shot\` | Use the prompt path. Training will make things worse. |
| 200–500 | \`marginal\` | Enough to try, not to trust. Hold out the recent fifth and beat the base model or discard it. |
| > 500 | \`ready\` | Worth a small-rank LoRA. Still split chronologically. |

Degenerate label distributions are flagged separately: if 95% of your
predictions missed, the calibration half is nearly all zeros and a model
trained on it learns to answer "no" to everything — accurate, and
useless.

## Known limitations

* **The compile dataset has a selection problem.** It contains theses you
  acted on, not theses you considered and dropped. The model learns to
  compile the kind of idea you commit to.
* **Thirty rows will not become three hundred quickly.** At a realistic
  rate of a few views a month, \`ready\` is years away for most users. The
  export exists so the data is accumulating in the right shape from day
  one, not because anyone should train tomorrow.
* **No evaluation harness ships with this.** The script prints a
  reminder to compare adapter against base on held-out theses by hand.
  Automating that comparison — and defining what "better" means for a
  structured-extraction task — is not done.
* **The calibration dataset is binary.** Each row is one Bernoulli draw
  against a stated probability, which is an extremely weak signal per
  example. This is the same small-n problem the Brier calibration in
  \`hone/journal/\` has, and it does not go away by moving it into a model.

## References

* Dettmers, T., Pagnoni, A., Holtzman, A., & Zettlemoyer, L. (2023).
  "QLoRA: Efficient Finetuning of Quantized LLMs." *NeurIPS 2023*.
* Hu, E. J., et al. (2021). "LoRA: Low-Rank Adaptation of Large Language
  Models." *ICLR 2022*.
* Brown, T., et al. (2020). "Language Models are Few-Shot Learners."
  *NeurIPS 2020* — the reason the prompt path works at n = 5.
`,Ju=`# Roadmap — taking Hone to the next level

Ideas ordered roughly by leverage: how much each moves the product per
unit of effort. Items marked ★ are the highest-conviction bets.

## Measurement (Part 1)

- ★ **Stated vs. revealed risk aversion.** Reverse-optimize the user's
  actual holdings to extract the γ their portfolio implies, and show it
  next to their questionnaire γ: "You answer like Tier 31 but invest
  like Tier 8." The gap is the single most shareable, most actionable
  insight the data can produce. (All the math already exists in
  \`black_litterman.implied_equilibrium_returns\` — this is a UI feature.)
- ★ **Loss aversion (prospect theory λ).** Add a short gain/loss-framed
  lottery block (Tanaka-Camerer-Nguyen style) and estimate λ alongside
  γ. Hedging then keys the put floor to λ (fear of losses) and the vol
  budget to γ (dislike of variance) — two-parameter personalization no
  mainstream tool has.
- **γ history and retest cadence.** Preferences drift with age, markets,
  and life events. Store every elicitation, chart the trajectory, prompt
  a quarterly retest. (Requires accounts — already scoped.)
- **Consistency diagnostics.** Surface the noise parameter μ to users as
  a "decision consistency" score; flag scale-sensitivity (different
  switch points at $2 vs $200 stakes) as its own insight.

## Risk expression (Part 2)

- ★ **Dollars and drawdowns, not volatility.** Translate every risk
  number into dollar terms on the user's actual balance, and add
  historical scenario replays (2008, 2020, 2022): "In a 2008, this
  portfolio loses ~$23,000; your tier tolerates ~$9,000."
- **CVaR / max-drawdown risk budget.** Offer expected-shortfall or
  drawdown as the budget the hedging engine targets instead of vol —
  closer to how people actually experience risk.
- **Risk drift alerts.** Recompute portfolio vol vs. tier budget on a
  schedule; email/push when the portfolio drifts more than N tiers hot.
  Turns a one-shot tool into a recurring relationship.
- **Regime awareness.** Flag when EWMA correlations spike vs. the
  long-run estimate ("diversification is currently weaker than normal").

## Portfolio & hedging (Part 3)

- ★ **One-click paper execution.** \`submit_order\` exists; wire an
  "Execute rebalance + hedge" button against the Alpaca paper account,
  then track realized before/after performance. Learning by doing is
  what converts trust into habit.
- **Live options chains.** Alpaca's options paper trading gives real
  strikes/premiums; replace indicative Black-Scholes hedge costs with
  executable quotes, and place the collar as a real paper order.
- **Transaction-cost & turnover penalty in MVO.** Stops the optimizer
  suggesting 1% dust trades; add a "minimum trade size" and a
  cost-adjusted certainty-equivalent comparison ("this rebalance is
  worth +0.8%/yr after costs").
- **Robust optimization.** Michaud-style resampling or worst-case
  (box-uncertainty) MVO so weights stop being twitchy to estimation
  error in μ.
- **Multiple simultaneous views with consistency check.** Warn when a
  user's views are internally contradictory given correlations.

## Product & trust

- **Accounts + persistence** (scoped: SQLite storage, session auth,
  encrypted key storage, saved profiles/views).
- **Plain-English explanations everywhere.** Every recommendation gets a
  "why": "Sell MSFT: it's 45% of your portfolio and contributes more
  variance than expected return at your tier."
- **Evidence page.** Backtest tier-matched portfolios vs. naive
  alternatives on risk-adjusted return and drawdown-behavior metrics;
  publish the methodology. The credibility asset for a math-forward
  product.
- **Education layer.** Every concept (γ, covariance, collar) gets a
  two-sentence tooltip; the product doubles as a financial-literacy
  course the user takes by accident.
- **Peer context.** "Your tier vs. the distribution of Hone users" —
  \`percentile_hint\` already computes the raw material.
- **Compliance posture.** Keep positioning as decision-support /
  education, not advice; revisit registered-advisor requirements before
  any real-money execution feature.

## Business

- ★ **B2B risk-profiling API.** Advisors are legally required to assess
  client risk tolerance, and incumbent tools are unfalsifiable
  three-bucket quizzes. White-label the Holt-Laury + MLE engine
  (questionnaire in, γ + tier + confidence interval out) for RIAs and
  fintechs. The retail app is the demo; the API is the revenue.
- **Freemium split.** Free: questionnaire, tier, demo pipeline. Paid:
  live account link, hedge plans, drift alerts, γ history.
`,Zu=`# Accounts & saved portfolios with Supabase

Hone ships with an **optional** authentication layer: users sign up / sign
in with email + password, and each user can save named portfolio snapshots
(their γ, tier, and views) and reload them later. It's powered by
[Supabase](https://supabase.com) (a hosted Postgres + auth service with a
generous free tier).

**It's off until you configure it.** With no Supabase keys, Hone runs
exactly as before — no login, nothing stored server-side, everything in the
browser. Turning it on is three steps and ~10 minutes.

---

## 1. Create a Supabase project

1. Sign up at [supabase.com](https://supabase.com) → **New project**.
2. Give it a name and a database password (you won't need the password for
   Hone). Wait ~2 minutes for it to provision.
3. In **Project Settings → API**, copy two values:
   - **Project URL** — e.g. \`https://abcdefghijkl.supabase.co\`
   - **anon public** key — a long JWT. This is safe to expose in the
     browser (it's the public key; Row-Level Security does the real
     protection). **Never** use the \`service_role\` key here.

## 2. Create the \`portfolios\` table (with Row-Level Security)

In the Supabase dashboard open **SQL Editor** and run this. It creates the
table and locks it down so every user can only ever see and modify their
**own** rows:

\`\`\`sql
create table public.portfolios (
  id         uuid primary key default gen_random_uuid(),
  user_id    uuid not null references auth.users (id) on delete cascade,
  name       text not null,
  data       jsonb not null,
  created_at timestamptz not null default now()
);

alter table public.portfolios enable row level security;

create policy "own rows: select" on public.portfolios
  for select using (auth.uid() = user_id);
create policy "own rows: insert" on public.portfolios
  for insert with check (auth.uid() = user_id);
create policy "own rows: delete" on public.portfolios
  for delete using (auth.uid() = user_id);

create index portfolios_user_idx on public.portfolios (user_id, created_at desc);
\`\`\`

Row-Level Security is the whole security model here: even though the anon
key is public, these policies mean the database itself refuses to return
or modify a row unless the request's authenticated user owns it.

## 2b. (For linked brokerages) the \`broker_links\` table

Only needed if you turned on [brokerage linking](BROKERAGES.md). Each user's
SnapTrade link is kept here so it follows them to other devices. Run:

\`\`\`sql
create table public.broker_links (
  user_id               uuid primary key references auth.users (id) on delete cascade,
  snaptrade_user_id     text not null,
  snaptrade_user_secret text not null,
  updated_at            timestamptz not null default now()
);

alter table public.broker_links enable row level security;

create policy "own link: select" on public.broker_links
  for select using (auth.uid() = user_id);
create policy "own link: insert" on public.broker_links
  for insert with check (auth.uid() = user_id);
create policy "own link: update" on public.broker_links
  for update using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "own link: delete" on public.broker_links
  for delete using (auth.uid() = user_id);
\`\`\`

The secret here can't be used on its own: every SnapTrade request also has to
be signed with your server's consumer key, which never leaves the server.

## 3. Configure email auth

In **Authentication → Providers → Email**, make sure Email is enabled.
For a smooth first run you may want to turn **"Confirm email" off** (under
Authentication → Providers → Email → *Confirm email*) so sign-ups work
without a verification round-trip; turn it back on for production and
configure the email templates/SMTP.

Add your site to the allowed redirect/site URLs under
**Authentication → URL Configuration** (e.g. \`https://studiohone.com\` and
\`http://localhost:8000\` for local dev).

## 4. Point Hone at your project

Edit \`hone/web/static/config.js\` and fill in the two values from step 1:

\`\`\`js
window.HONE_CONFIG = {
  supabaseUrl: "https://abcdefghijkl.supabase.co",
  supabaseAnonKey: "eyJhbGciOi...your-anon-key...",
};
\`\`\`

Redeploy (or restart \`python -m hone serve\`). That's it — a **Sign in /
Sign up** control now appears at the top of the app, and finishing a run
shows a **Save this portfolio** button. Saved portfolios are listed under
**Saved portfolios**, and loading one drops you back into the flow with its
γ and views restored.

### Keeping keys out of the repo (optional, for production)

\`config.js\` holds only public values, so committing it is acceptable. If
you'd rather not, add \`hone/web/static/config.js\` to \`.gitignore\` and write
it at deploy time from environment variables — for example a small entry in
your Docker start command:

\`\`\`sh
cat > hone/web/static/config.js <<EOF
window.HONE_CONFIG = { supabaseUrl: "$SUPABASE_URL", supabaseAnonKey: "$SUPABASE_ANON_KEY" };
EOF
\`\`\`

then set \`SUPABASE_URL\` / \`SUPABASE_ANON_KEY\` in your host's environment
(Render → Environment, Fly → secrets).

---

## How it works (for the curious)

- The browser talks to Supabase's REST/GoTrue HTTP APIs directly — no SDK,
  no CDN script, so it stays within Hone's self-contained model.
- \`signUp\` / \`signIn\` hit \`/auth/v1/signup\` and
  \`/auth/v1/token?grant_type=password\`; the returned session (a JWT) is kept
  in \`localStorage\` and sent as a Bearer token on every data call.
- Saving a portfolio \`POST\`s to \`/rest/v1/portfolios\`; listing/deleting use
  the same PostgREST endpoint. RLS scopes every call to the signed-in user.
- **What's saved:** γ, tier, the demo/live flag, and your views — never your
  Alpaca keys (those stay only in your browser and are never persisted).

## Security notes

- The anon key is *designed* to be public; your data is protected by the
  RLS policies above, not by hiding the key. Do not paste the
  \`service_role\` key into \`config.js\`.
- Hone stores no brokerage *passwords* anywhere: brokerages are linked on
  SnapTrade's own page. The \`broker_links\` table holds the user's SnapTrade
  link, readable only by that user, and useless without the server's
  SnapTrade consumer key. Alpaca keys live only in the browser session.
- If you enabled \`HONE_ACCESS_PASSWORD\` (the site-wide gate), that and
  Supabase auth are independent layers — you can use either or both.
`,e2=`# Tail risk: CVaR as a second opinion

## Why variance is not enough

Mean-variance optimization is the backbone of Hone's main flow, and it
earns its place: it is the objective Black-Litterman blends views into,
and the quadratic utility it maximizes is the standard second-order
approximation of the CRRA preferences the questionnaire elicits. But it
carries two assumptions that do not survive contact with markets.

**Variance is symmetric.** It penalizes a 10% gain exactly as hard as a
10% loss. No investor feels that way, and the elicited γ is a statement
about losses.

**Σ assumes second moments tell the story.** Real returns are
left-skewed and fat-tailed, and correlations converge toward one exactly
when diversification is being counted on. A portfolio can look
well-behaved in the covariance matrix and still have a tail that takes
half of it. In crypto this is not a subtlety — the synthetic universe in
\`hone/crypto/\` uses Student-t innovations with 4 degrees of freedom
precisely because that is what the data looks like.

## What CVaR asks instead

Conditional Value-at-Risk at level β is the **average loss across the
worst 1 − β of outcomes**. Not the threshold you cross — the average of
everything past it.

| Measure | Question it answers |
|---|---|
| Volatility | How much does this bounce around? |
| VaR | How bad is the loss I only exceed 5% of the time? |
| **CVaR** | **When I do exceed it, how bad is it on average?** |

VaR is what most people mean by "worst case" and is the weakest of the
three: it says nothing whatsoever about the losses beyond it, and it is
not a coherent risk measure in the Artzner et al. (1999) sense — it can
penalize diversification, telling an investor that splitting a position
made them riskier. CVaR is coherent. Hone shows VaR anyway, next to
CVaR, because putting them side by side is the clearest way to make the
difference concrete.

## The method

Rockafellar & Uryasev (2000) is what makes this tractable. For a set of
scenarios, minimizing

\`\`\`
F_β(w, ζ) = ζ + 1/((1−β)T) · Σ_t max(0, −r_t·w − ζ)
\`\`\`

jointly over the weights and an auxiliary ζ minimizes CVaR, and the
optimal ζ turns out to be the VaR. The \`max()\` linearizes with one slack
variable per scenario, so the whole problem is a **linear program** — no
local optima, no convergence tuning, no covariance matrix at all. It
stays linear when an expected-return term is added, which is what makes
the mean-CVaR frontier cheap to trace.

Scenarios are overlapping 21-period simple returns from the user's own
price history — simple, not log, because portfolio return is a weighted
sum of simple returns and CVaR is a claim about wealth.

## Two portfolios, not one

**Minimum CVaR (risk-first)** minimizes the tail and *ignores expected
returns entirely*. That sounds like a limitation and is closer to a
feature: return forecasts are the least reliable input in the whole
pipeline, and a portfolio that never sees them cannot be wrecked by
getting them wrong.

**Mean-CVaR at your γ** trades tail against return at the rate the
user's elicited risk aversion implies. Hone's premise is that the risk
knob is measured rather than chosen, so a CVaR mode with a hand-picked
coefficient would be a different product wearing the same clothes.
\`kappa_from_gamma\` matches the marginal rate of substitution between
return and risk:

\`\`\`
mean-variance :  dU/dσ = −γσ
mean-CVaR     :  dU/dσ = −κ·k        k = φ(z_β)/(1−β)
⇒  κ = γ·σ_ref / k
\`\`\`

This is a **local** match at a reference volatility, and the claim is
deliberately narrow: it makes γ mean roughly the same thing in both
modes. It is not an equivalence — the entire point of CVaR is that the
distribution is not normal, and \`k\` is a normal-distribution factor.
Where the two modes disagree, the disagreement is the information.

The expected returns fed to the mean-CVaR arm are the **equilibrium
prior** Π = δΣw, not sample means. Two years of sample means are noise,
and feeding them to an optimizer is the classic error that gave
mean-variance its reputation.

## Where this sits in the product

It is a **second opinion, not a replacement**. The main flow stays
variance-based, because that is what Black-Litterman blends views into
and what the γ→volatility risk budget in the hedging engine is built on.
The tail page tells the user what that choice costs them in the tail,
in dollars.

## Known limitations

* **Overlapping windows share data.** 700 overlapping monthly windows are
  nothing like 700 independent observations. The effective sample in the
  tail is far smaller than the count suggests, and the page says so.
* **The tail is thin by construction.** At β = 0.95 over 500 scenarios the
  average is taken over 25 points. That is thin evidence, and it is why
  the 99% option carries a warning: at that level it is five points, and
  an average of five points is not an estimate.
* **History is not a forecast.** The worst month in the data is not the
  worst month there is. A user whose history happens to exclude a crash
  gets a CVaR that reflects that luck.
* **Pure risk minimizers concentrate.** Uncapped, the minimum-CVaR
  portfolio is often a *single name* — whatever happened to be quietest
  in-sample. This is the same pathology minimum-variance optimizers have,
  and it is why \`max_weight\` is not optional in the product. There is a
  test pinning the behaviour so nobody removes the cap thinking the
  objective will hold the line on its own.
* **No transaction costs.** Adopting these weights implies trades that are
  not priced anywhere in Hone yet.

## References

* Rockafellar, R. T., & Uryasev, S. (2000). "Optimization of Conditional
  Value-at-Risk." *Journal of Risk* 2(3), 21–41.
* Rockafellar, R. T., & Uryasev, S. (2002). "Conditional value-at-risk
  for general loss distributions." *Journal of Banking & Finance* 26(7).
* Artzner, P., Delbaen, F., Eber, J.-M., & Heath, D. (1999). "Coherent
  measures of risk." *Mathematical Finance* 9(3), 203–228.
* Krokhmal, P., Palmquist, J., & Uryasev, S. (2002). "Portfolio
  optimization with conditional value-at-risk objective and constraints."
  *Journal of Risk* 4(2).
`,n2=`# Hone — know your number

## The one-liner

Hedge funds quantify risk tolerance before they invest a dollar. Retail
investors get a three-question quiz and a "moderate" sticker. Hone gives
individual investors the same measurement science the professionals use —
and then makes every portfolio decision answer to it.

## The problem

Every brokerage onboarding asks some version of "How would you feel if
your portfolio dropped 20%?" and sorts you into Conservative, Moderate,
or Aggressive. That label then quietly governs the most consequential
financial decisions of your life — while being unfalsifiable, unstable,
and untethered to any model of behavior.

Meanwhile, the quantitative machinery that institutions run on — utility
theory, covariance estimation, portfolio optimization, systematic
hedging — has been fully described in public academic literature for
decades. It never reached individuals, not because it's secret, but
because it was never packaged for them.

The result is a familiar failure mode: investors take on more risk than
they can psychologically carry, discover this only inside a drawdown,
and sell at the bottom. The damage isn't caused by markets. It's caused
by the mismatch between a portfolio and the person holding it.

## What Hone does

Hone is built on a simple conviction: **your risk tolerance is a
measurable number, and your portfolio should be built around it.**

**1. Measure.** Instead of asking how you'd feel about losses, Hone
observes what you choose. A Holt-Laury lottery experiment — the standard
instrument in experimental economics since 2002 — presents thirty
structured choices between safer and riskier gambles at escalating
stakes. A maximum-likelihood engine fits a constant-relative-risk-
aversion utility model to your choices, separating your true preference
from decision noise, and produces a point estimate of your risk-aversion
parameter γ with a confidence interval. You're placed in one of fifty
tiers, from aggressively risk-seeking to highly risk-averse. Not a
vibe — a coefficient.

**2. Diagnose.** Hone connects to your brokerage account, reads your
actual holdings, and builds the statistical fingerprint of your
portfolio: how your assets move together, and how much risk you're
really carrying. Because the same math runs in reverse, Hone can also
infer the risk tolerance your portfolio *implies* — and show you the gap
between who you say you are and how your money is invested.

**3. Reweight.** When you have conviction — "I think this stock reaches
$400 within a year, and I'm 60% confident" — Hone doesn't ignore it or
blindly obey it. Black-Litterman, the model built at Goldman Sachs for
exactly this purpose, blends your view against market equilibrium in
proportion to your stated confidence. Mean-variance optimization then
rebuilds your weights with your measured γ setting the risk appetite.
Your conviction, disciplined by your own number.

**4. Hedge.** If your portfolio runs hotter than your tier can tolerate,
Hone sizes the professional's toolkit to close the gap: an index short
that brings volatility exactly to your budget, protective puts with a
floor set by your risk aversion, or a zero-cost collar that trades
upside you don't need for protection you do. Costed, explained, and
sized to *you*.

## What Hone is not

Hone is not investment advice, not a robo-advisor that hides the
machinery, and not a signal service. It doesn't predict markets. It
makes one promise only: the risk you carry will be the risk you chose,
measured honestly. Every recommendation shows its work — the model, the
inputs, and the assumptions are on the table.

## The goal

Financial self-knowledge, quantified. In the long run, Hone wants
"What's your risk number?" to be as answerable as "What's your credit
score?" — and wants every retail portfolio to be able to justify itself
against the number of the person who owns it.

The gap between institutional and individual investing was never about
intelligence. It was about tooling. That gap is now closeable.

---

*Hone runs on the Holt-Laury multiple price list (2002), CRRA expected
utility with Fechner-noise maximum likelihood estimation, Ledoit-Wolf
covariance shrinkage, Black-Litterman equilibrium blending with Idzorek
confidence mapping, Markowitz mean-variance optimization, and
Merton-rule risk budgeting — the standard quantitative canon, applied to
one person at a time.*
`,t2=`# Hone

Hedge-fund-grade risk tools for retail investors, in three parts:

1. **Quantify your risk aversion** — eight adaptive questions, each chosen
   to maximize what its answer reveals, place your risk-aversion
   parameter **γ** in one of **50 risk tiers** with a credible interval.
   The classic 30-question Holt-Laury menu with CRRA maximum-likelihood
   estimation is still available and estimates the same model.
2. **Measure your portfolio's risk** — an Alpaca paper-trading client
   pulls your holdings and price history, and a business-side
   covariance calculator (sample / EWMA / Ledoit-Wolf shrinkage) builds
   the covariance matrix Σ.
3. **Reweight and hedge** — name a stock you like with a target price
   and a confidence level; Black-Litterman blends that view with the
   equilibrium implied by your current holdings, γ-aware Mean-Variance
   Optimization reweights the portfolio, and the hedging engine
   proposes shorts and option overlays (protective puts, zero-cost
   collars) sized so the hedged portfolio matches your risk budget.

## Install

\`\`\`bash
pip install -e ".[dev]"
python -m pytest            # full test suite, no network needed
\`\`\`

## Web app

Everything below is also available in the browser:

\`\`\`bash
python -m hone serve                 # http://127.0.0.1:8000
\`\`\`

The browser app is organised around **tools you can open in any order**,
each at its own URL, rather than a step-by-step flow:

| Workspace tool (\`/:product/app/...\`) | What it does |
|---|---|
| Overview | Summary, launch cards, current vs. model-proposed allocation |
| Risk aversion (\`risk\`) | Eight-question adaptive estimate (or the classic 30), with uncertainty; stated vs. revealed risk |
| Investment theses (\`theses\`) | Editable price-target views with a live allocation beside them; plain-English compiler; "More view types" (entropy pooling) |
| Portfolio (\`portfolio\`) | Current vs. proposed, one expandable explanation per change, sensitivity, commit views to the journal |
| Hedging (\`hedging\`) | Hedge plan, stress scenarios, tail risk (CVaR) |
| Track record (\`record\`) | Decision journal, calibration, training-data export |
| Backtest (\`backtest\`) | Walk-forward backtest at your risk level, with the behaviour gap |
| Data & account (\`settings\`) | Sample data, linked brokerages, or an Alpaca paper account; optional sign-in |

Prediction Markets has its own tools: \`hedge\` (size an income hedge) and
\`markets\` (browse the Kalshi catalog). Public pages per product: overview,
\`how-it-works\`, \`methodology\`, \`backtests\`, \`setup\` — the last three render
the files in \`docs/\` verbatim. Everything runs on **sample data** with no
Alpaca account; switch to your paper account under *Data & account* (keys
are sent per request and never stored server-side), or leave them blank to
use the server's \`ALPACA_API_KEY\` / \`ALPACA_SECRET_KEY\`. The JSON API is
documented at \`/docs\` (OpenAPI) when the server is running.

### Working on the frontend

The UI is a React app (Vite) in \`frontend/\`. Its production build is
written to \`hone/web/static/\` and **committed**, so deploys need no Node
toolchain.

\`\`\`bash
cd frontend
npm install
npm run dev     # http://localhost:5173, proxies /api to python -m hone serve on :8000
npm run build   # rebuild hone/web/static/ — commit the result
\`\`\`

Where things live: \`src/lib/\` (API client, persisted state, formatting,
product definitions), \`src/components/\` (shared UI), \`src/pages/\` (one
folder per area), \`src/styles/global.css\` (design tokens — edit colours
there), \`src/reactbits/\` (components from [React Bits](https://reactbits.dev):
AnimatedContent, SlideCommit, SpotlightCard, RubberSegment, SquishSwitch).

## Layout

\`\`\`
hone/
├── risk_profile/    # questionnaire, MLE, 50 tiers, DOSE adaptive elicitation
├── market_data/     # Alpaca client, SnapTrade brokerages, covariance
├── optimization/    # MVO, views, Black-Litterman, CVaR, entropy pooling
├── hedging/         # shorts, puts, collars, Black-Scholes
├── journal/         # decision journal, Brier scoring, learned confidence
├── llm/             # Conviction Compiler (Claude + offline parser)
├── crypto/          # the crypto product's universe and parameters
├── prediction/      # Hone Markets: event-contract hedging, Kalshi catalog
├── backtest/        # walk-forward engine + conviction population study
├── web/             # FastAPI JSON API; static/ holds the built React app
├── pipeline.py      # end-to-end flow
└── cli.py           # \`python -m hone ...\` (incl. \`serve\`)
frontend/            # React source for the web app (built into hone/web/static/)
\`\`\`

## Hosting it on a domain

The app ships with a \`Dockerfile\` and configs for the two easiest hosts.
Two environment variables control the deployment posture:

| Variable | Effect |
|---|---|
| \`HONE_PUBLIC=1\` | The server refuses to use its own \`ALPACA_*\` env keys — every visitor must enter their own keys in the page. **Set this on anything strangers can reach** (the Dockerfile sets it by default). |
| \`HONE_ACCESS_PASSWORD\` | When set, the whole site sits behind HTTP Basic auth with this password (any username). Use it for a private personal deployment. |
| \`SNAPTRADE_CLIENT_ID\`, \`SNAPTRADE_CONSUMER_KEY\` | Turn on **linked brokerages**: users read real holdings from Schwab, Fidelity, Robinhood and more. See [docs/BROKERAGES.md](docs/BROKERAGES.md). |
| \`ALPACA_DATA_API_KEY\`, \`ALPACA_DATA_SECRET_KEY\` | Alpaca keys used only for price history (never to read an account), so they're safe on a public server. Linked-brokerage portfolios need them. |

\`/api/health\` is always open for platform health checks.

> **Why not Vercel?** Tried and hit a hard wall: Vercel Python functions
> cap at 250 MB uncompressed, and this app's numpy+scipy+pandas+fastapi
> stack exceeds it once complete. The hosts below run the Docker image
> and have no such limit.

### Option A — Render (Docker, ~10 minutes)

1. Push this repo to GitHub (already done if you're reading this there).
2. At [render.com](https://render.com): **New + → Blueprint**, pick this
   repo — it reads \`render.yaml\` and builds the Docker image.
3. You immediately get \`https://hone-XXXX.onrender.com\` with TLS.
4. Custom domain: service **Settings → Custom Domains → Add**, enter
   \`studiohone.com\`. Render shows you the DNS records to create at your
   registrar: a \`CNAME\` from \`www\` to your onrender hostname (and an
   \`A\`/\`ALIAS\` record for the apex). Certificates are provisioned
   automatically once DNS propagates.

### Option B — Fly.io

\`\`\`bash
fly launch --copy-config --no-deploy    # uses fly.toml
fly deploy
fly certs add studiohone.com            # prints the DNS records to add
\`\`\`

### Option C — your own VPS (full control)

\`\`\`bash
docker build -t hone . && docker run -d -p 127.0.0.1:8000:8000 hone
\`\`\`

Then put [Caddy](https://caddyserver.com) in front for automatic HTTPS —
a 2-line \`Caddyfile\`:

\`\`\`
studiohone.com {
    reverse_proxy 127.0.0.1:8000
}
\`\`\`

and point your domain's \`A\` record at the server's IP.

### Deployment posture

- **Public site** (default in the Dockerfile): keep \`HONE_PUBLIC=1\`, do
  NOT set \`ALPACA_*\` on the server. Visitors bring their own paper keys,
  which are sent per request and never stored.
- **Personal site**: set \`HONE_ACCESS_PASSWORD\`, optionally set your
  \`ALPACA_*\` keys as server env vars, and \`HONE_PUBLIC=0\` so the page
  works without typing keys.
- There are no user accounts and no server-side storage — every request
  is stateless. If you want saved profiles/portfolios per user, that's
  the next build step.

## Hone Crypto (side product, same protocol)

The same engine runs a crypto variant — identical elicitation, covariance,
Black-Litterman and MVO protocol, with crypto parameters (365-day year,
BTC as market proxy, real crypto drawdowns for stress tests, stablecoins
instead of options as the hedge leg):

\`\`\`bash
python -m hone crypto-demo                  # full crypto pipeline, synthetic data
python -m hone serve --asset-class crypto   # the crypto site
HONE_ASSET_CLASS=crypto python -m hone serve   # same thing via env
\`\`\`

**One deployment serves all three.** The site has product tabs: \`/\` is the
stocks product, \`/crypto\` is the crypto one and \`/prediction-markets\` is
Hone Markets (below) — so \`studiohone.com/crypto\`
works with no extra service, no second domain, and no DNS changes. The
asset class resolves per request (URL path, or \`?asset_class=crypto\` on
API calls), and each product keeps its own saved state in the browser.

Setting \`HONE_ASSET_CLASS=crypto\` still pins an entire deployment to one
product if you ever want them served separately.

The research basis, every parameter difference, and the known limitations
are documented in [docs/CRYPTO_RESEARCH.md](docs/CRYPTO_RESEARCH.md).

## Hone Markets (third product): hedging a paycheck

The third tab, \`studiohone.com/prediction-markets\`, turns the same
machinery around. The stocks product asks how much of a risky asset you
should hold given your γ; this one is for people whose *income* is the
risky asset — a ski instructor whose season depends on Aspen snowfall, an
ad freelancer whose bookings follow ad budgets, a recruiter whose fees
follow hiring. Kalshi lists event contracts on exactly those things, and a
contract that pays when the season goes badly is a hedge for a position
you never chose.

* **Same γ, same utility, same certainty equivalent** — the questionnaire
  is shared, and a number measured on the Stocks tab is offered here.
* **Insurance first, then the bet.** Maximizing expected CRRA utility of
  end-of-season wealth gives a position that always splits into a pure
  hedge (your loss × how tightly the market tracks it — the analogue of
  the beta-sized index short) and a speculative tilt on the gap between
  your odds and the price, shrunk by γ. The page labels both.
* **What it is worth, and the most to pay.** The certainty-equivalent
  gain prices the hedge in dollars at your γ; a closed-form reservation
  price \`c_max = E[U′(W₀)·B] / E[U′(W₀)]\` is the ceiling above which the
  tool shows no position — the Merton risk budget for a binary event.
* **Your odds against the market** are blended the Black-Litterman way,
  with the journal's calibration map applied to your confidence once it
  has scored enough of your predictions. Basis risk is a slider, and the
  hedge shrinks to ρ·L.
* **Live Kalshi data, no account.** 41 curated series in six groups —
  snow and ski-resort openings, ad-spend indices, labor, housing and
  rates, travel, fuel — read from the public API with a bundled snapshot
  as the fallback. Hone never places orders.

\`\`\`bash
python research/prediction/fetch_kalshi_snapshot.py   # refresh the bundled snapshot
HONE_KALSHI_LIVE=0 python -m hone serve                 # serve the snapshot only
\`\`\`

Theory, derivations, the catalog and the limitations are in
[docs/PREDICTION_MARKETS.md](docs/PREDICTION_MARKETS.md).

## Linked brokerages (optional)

Users can link every brokerage they use (Schwab, Fidelity, Robinhood,
Interactive Brokers, Webull, Coinbase and more) through
[SnapTrade](https://snaptrade.com), and Hone combines all their accounts into
one portfolio. Links are read-only, users sign in on SnapTrade's page (Hone
never sees a brokerage password), and positions Hone can't model (cash,
options, mutual funds, non-USD listings) are listed with the reason rather
than silently dropped. Prices still come from Alpaca market data. Off until
\`SNAPTRADE_CLIENT_ID\` / \`SNAPTRADE_CONSUMER_KEY\` are set; on a public server,
linking requires sign-in. Setup: [docs/BROKERAGES.md](docs/BROKERAGES.md).

## Accounts & saved portfolios (optional)

Hone has an optional Supabase-powered auth layer: users sign in and save
named portfolio snapshots (γ, tier, views) to reload later. It's **off
until configured** — with no keys, Hone runs fully in-browser as
described above. To turn it on, follow [docs/SUPABASE.md](docs/SUPABASE.md)
(create a project, run the provided SQL with Row-Level Security, and fill
in \`hone/web/static/config.js\`).

## Checked against independent libraries

The standard math in Hone runs on widely used open-source libraries, and
Hone's own implementations are kept as fallbacks and checked against them
(\`tests/test_reference_libraries.py\`):

| Piece | Engine | Hone's own version |
|---|---|---|
| Portfolio optimization (γ-aware mean-variance) | [PyPortfolioOpt](https://github.com/PyPortfolio/PyPortfolioOpt) with the Clarabel interior-point solver | SciPy SLSQP: same utility to within 1e-7 on 100 random problems |
| Black-Litterman posterior | PyPortfolioOpt, with Hone's confidence → Ω mapping | Same formula: agrees to ~1e-12, and both match a 50-digit computation |
| Ledoit-Wolf covariance | scikit-learn | Agrees to ~1e-16 |
| Minimum-CVaR | Hone's own LP (HiGHS) | Checked against PyPortfolioOpt's \`EfficientCVaR\` |

The cross-check found one real bug: the old Black-Litterman code inverted
τΣ and lost precision when two holdings move almost identically (SPY and
VOO, GOOG and GOOGL), shifting expected returns by ~0.4 percentage points.
Both engines now use the form that only inverts the small views matrix.

What stays Hone's own: the risk questionnaire, the confidence calibration,
the view conventions, the hedging engine, entropy pooling, the backtests,
and income hedging. Those are what Hone is for.

## Measuring risk aversion in eight questions

The 30-question Holt-Laury menu is still there, but the default is now
adaptive (\`hone/risk_profile/dose.py\`): a Bayesian posterior over (γ, μ) is
updated after every answer, and each question is chosen to maximize the
information its answer is expected to carry. Eight questions match thirty
fixed ones — and beat them by a factor of four to five for risk-averse
users, because the classic menu's indifference points top out around γ ≈ 1.4
and it simply cannot see above that. The page shows the posterior narrowing
as you answer, and the credible interval is carried forward rather than
rounded away. Method, the simulation results, and the limitations are in
[docs/ADAPTIVE_ELICITATION.md](docs/ADAPTIVE_ELICITATION.md).

## Teaching a model your habits

Your resolved predictions are the only data that could teach a model how *you*
write and what your language turns out to be worth. Hone ships two paths and
is blunt about which one works at your scale. **In-context personalization**
(\`hone/llm/personalize.py\`) puts your own resolved examples — outcome-balanced,
plus your realized hit rate — into the compiler's prompt. No GPU, active from
five predictions, better every time one resolves. **QLoRA export**
(\`hone/llm/export.py\`, \`training/train_qlora.py\`) builds a fine-tuning dataset
whose calibration labels are *realized outcomes* rather than stated confidence
— so a model learns what your language predicts, not how sure you claim to be.
It refuses to train below 200 examples, because thirty rows produce a model
that has memorized them and is worse than the base on the thirty-first.
See [docs/QLORA.md](docs/QLORA.md).

## The behaviour gap

Every backtest here assumed you held the strategy through everything it did.
Almost nobody does. \`hone/backtest/behavior.py\` drops that assumption: your γ
sets a tolerable drawdown through the same Merton budget the hedge page uses,
you're modelled as capitulating past it, and you buy back only once the market
has climbed 10% off its low — which is what makes it expensive, because it
means buying above the bottom. Trading costs and the cash rate are both
charged. The evidence page now shows what the same strategies returned *as
you'd have held them*. The tier-matched portfolio has the smallest gap of the
diversified strategies, which is the whole argument for sizing a portfolio to
what you can sit through. See [docs/BEHAVIOR_GAP.md](docs/BEHAVIOR_GAP.md),
including the case where capitulating is the right call.

## Views that aren't price targets

Black-Litterman needs a linear statement about an expected return under a
normal distribution. Most convictions aren't that shape: *a one-in-three
chance of a bad drawdown*, *I'm sure A beats B but couldn't price either*,
*if Bitcoin breaks, Ethereum breaks harder*. Forcing those through a
price-target box makes users invent numbers, and an invented number is
indistinguishable from a real one by the time it reaches the optimizer.
\`hone/optimization/entropy_pooling.py\` takes them as constraints on scenario
probabilities instead, and returns the minimum-relative-entropy posterior —
the update that adds nothing beyond what you actually asserted (Meucci 2008).
It reports what your views cost in effective scenarios, and says so when
they've collapsed the sample. Chained with CVaR, it gives a path from belief
to portfolio that assumes normality nowhere.
See [docs/FLEXIBLE_VIEWS.md](docs/FLEXIBLE_VIEWS.md).

## Tail risk, as a second opinion

Variance treats a good month and a bad month identically and assumes the
covariance matrix captures the joint distribution. \`hone/optimization/cvar.py\`
adds the blunter question — *when it goes badly, how badly?* — via
Conditional Value-at-Risk, the average loss across the worst 5% of months,
read straight off price history rather than assumed from Σ. Rockafellar and
Uryasev's formulation makes it a linear program, so it solves exactly. Two
portfolios come back: the **risk-first** one that minimizes the tail and
never looks at expected returns, and the **γ-matched** one that trades tail
for return at the rate your elicited risk aversion implies. The main flow
stays variance-based; this page prices what that choice costs you.
See [docs/TAIL_RISK.md](docs/TAIL_RISK.md).

## The conviction loop

Two features turn the pipeline above into something that improves with use.

**The Conviction Compiler** (\`hone/llm/\`) takes a thesis in plain English —
"I think Nvidia runs to $250 by the summer, fairly confident" — and compiles
it into the structured view the optimizer needs: ticker, entry price, target,
horizon, confidence. Claude does this when \`ANTHROPIC_API_KEY\` is set;
otherwise a deterministic parser handles it with no network and no key. The
result is a **proposal**: every field lands in an editable form with the
guessed ones marked, and nothing reaches Black-Litterman until the user
confirms it. The model is explicitly forbidden from inventing price targets —
it translates intent, and the server supplies live prices.

**The decision journal** (\`hone/journal/\`) logs every view at the moment it is
acted on, at the server's price, and scores it when its horizon elapses. The
accumulated record yields a Brier score, a reliability curve and a fitted map
from what the user *says* to what their history justifies — which is then
applied to future views, disclosed on screen, and switchable off. Confidence
is the one number in Hone the user supplies rather than the system measures,
and it is the lever controlling how far the portfolio tilts; this is how it
stops being taken on trust. The correction is deliberately gentle, and that
is an empirical result rather than caution: a simulated population of
investors showed that replacing stated confidence *outright* with a realized
hit rate loses more often than it wins, because it taxes anyone with genuine
edge. Confidence handling is a guardrail, not an edge. The method, the guards
against over-correcting on thin evidence, and the honest limitations are in
[docs/CALIBRATION.md](docs/CALIBRATION.md); the evidence is in
[docs/BACKTEST_CONVICTION.md](docs/BACKTEST_CONVICTION.md).

\`\`\`bash
pip install -e ".[llm]"        # optional: enables the Claude compiler
export ANTHROPIC_API_KEY=...   # without it, the offline parser is used
\`\`\`

## More docs

- [docs/VISION.md](docs/VISION.md) — what Hone is and why.
- [docs/ADAPTIVE_ELICITATION.md](docs/ADAPTIVE_ELICITATION.md) — DOSE: eight adaptive questions instead of thirty.
- [docs/BACKTEST_CONVICTION.md](docs/BACKTEST_CONVICTION.md) — does any of the conviction machinery actually help, and for whom.
- [docs/TAIL_RISK.md](docs/TAIL_RISK.md) — CVaR, why variance isn't enough, and what the tail page does not know.
- [docs/FLEXIBLE_VIEWS.md](docs/FLEXIBLE_VIEWS.md) — entropy pooling: probability, ranking and conditional views.
- [docs/BEHAVIOR_GAP.md](docs/BEHAVIOR_GAP.md) — what you'd actually have got, once you're allowed to panic.
- [docs/QLORA.md](docs/QLORA.md) — personalizing the compiler: few-shot now, fine-tuning when the data justifies it.
- [docs/CALIBRATION.md](docs/CALIBRATION.md) — the decision journal, Brier scoring, and learned confidence.
- [docs/ROADMAP.md](docs/ROADMAP.md) — where it's going.
- [docs/BROKERAGES.md](docs/BROKERAGES.md) — linking real brokerages through SnapTrade.
- [docs/SUPABASE.md](docs/SUPABASE.md) — enabling accounts & saved portfolios.
- [docs/CRYPTO_RESEARCH.md](docs/CRYPTO_RESEARCH.md) — Hone Crypto: literature, parameters, limitations.
- [docs/PREDICTION_MARKETS.md](docs/PREDICTION_MARKETS.md) — Hone Markets: hedging cyclical income with Kalshi event contracts.

## Disclaimers

This is analytical tooling, not investment advice. Option costs are
indicative Black-Scholes values — always use live quotes for execution.
The Alpaca integration targets the **paper-trading** API.
`,i2=`asset_class,gamma,skill,overconfidence,diag_stated_confidence,diag_mean_calibrated_confidence,diag_final_calibrated_confidence,diag_directional_hit_rate,diag_surprise_hit_rate,diag_views_resolved
crypto,0.5,0.0,1.0,0.314,0.06763068274751194,0.054833333333333345,0.51325,0.50575,100.0
crypto,0.5,0.0,2.0,0.628,0.06763068274751194,0.054833333333333345,0.51325,0.50575,100.0
crypto,0.5,0.2,1.0,0.38973190358856497,0.1450614825861334,0.15671428571428572,0.58175,0.572,100.0
crypto,0.5,0.2,2.0,0.7794638071771299,0.1450614825861334,0.15671428571428572,0.58175,0.572,100.0
crypto,0.5,0.4,1.0,0.4833858326082366,0.2298480361700705,0.2680952380952381,0.6407499999999999,0.635,100.0
crypto,0.5,0.4,2.0,0.9667716652164732,0.2298480361700705,0.2680952380952381,0.6407499999999999,0.635,100.0
crypto,1.2,0.0,1.0,0.314,0.06763068274751194,0.054833333333333345,0.51325,0.50575,100.0
crypto,1.2,0.0,2.0,0.628,0.06763068274751194,0.054833333333333345,0.51325,0.50575,100.0
crypto,1.2,0.2,1.0,0.38973190358856497,0.1450614825861334,0.15671428571428572,0.58175,0.572,100.0
crypto,1.2,0.2,2.0,0.7794638071771299,0.1450614825861334,0.15671428571428572,0.58175,0.572,100.0
crypto,1.2,0.4,1.0,0.4833858326082366,0.2298480361700705,0.2680952380952381,0.6407499999999999,0.635,100.0
crypto,1.2,0.4,2.0,0.9667716652164732,0.2298480361700705,0.2680952380952381,0.6407499999999999,0.635,100.0
crypto,2.5,0.0,1.0,0.314,0.06763068274751194,0.054833333333333345,0.51325,0.50575,100.0
crypto,2.5,0.0,2.0,0.628,0.06763068274751194,0.054833333333333345,0.51325,0.50575,100.0
crypto,2.5,0.2,1.0,0.38973190358856497,0.1450614825861334,0.15671428571428572,0.58175,0.572,100.0
crypto,2.5,0.2,2.0,0.7794638071771299,0.1450614825861334,0.15671428571428572,0.58175,0.572,100.0
crypto,2.5,0.4,1.0,0.4833858326082366,0.2298480361700705,0.2680952380952381,0.6407499999999999,0.635,100.0
crypto,2.5,0.4,2.0,0.9667716652164732,0.2298480361700705,0.2680952380952381,0.6407499999999999,0.635,100.0
crypto,5.0,0.0,1.0,0.314,0.06763068274751194,0.054833333333333345,0.51325,0.50575,100.0
crypto,5.0,0.0,2.0,0.628,0.06763068274751194,0.054833333333333345,0.51325,0.50575,100.0
crypto,5.0,0.2,1.0,0.38973190358856497,0.1450614825861334,0.15671428571428572,0.58175,0.572,100.0
crypto,5.0,0.2,2.0,0.7794638071771299,0.1450614825861334,0.15671428571428572,0.58175,0.572,100.0
crypto,5.0,0.4,1.0,0.4833858326082366,0.2298480361700705,0.2680952380952381,0.6407499999999999,0.635,100.0
crypto,5.0,0.4,2.0,0.9667716652164732,0.2298480361700705,0.2680952380952381,0.6407499999999999,0.635,100.0
crypto,8.0,0.0,1.0,0.314,0.06763068274751194,0.054833333333333345,0.51325,0.50575,100.0
crypto,8.0,0.0,2.0,0.628,0.06763068274751194,0.054833333333333345,0.51325,0.50575,100.0
crypto,8.0,0.2,1.0,0.38973190358856497,0.1450614825861334,0.15671428571428572,0.58175,0.572,100.0
crypto,8.0,0.2,2.0,0.7794638071771299,0.1450614825861334,0.15671428571428572,0.58175,0.572,100.0
crypto,8.0,0.4,1.0,0.4833858326082366,0.2298480361700705,0.2680952380952381,0.6407499999999999,0.635,100.0
crypto,8.0,0.4,2.0,0.9667716652164732,0.2298480361700705,0.2680952380952381,0.6407499999999999,0.635,100.0
`,r2=`asset_class,gamma,skill,overconfidence,diag_stated_confidence,diag_mean_calibrated_confidence,diag_final_calibrated_confidence,diag_directional_hit_rate,diag_surprise_hit_rate,diag_views_resolved
equities,0.5,0.0,1.0,0.314,0.0711545415170822,0.05010526315789472,0.5108333333333334,0.4913888888888889,90.0
equities,0.5,0.0,2.0,0.628,0.0711545415170822,0.05010526315789472,0.5108333333333334,0.4913888888888889,90.0
equities,0.5,0.2,1.0,0.38973190358856497,0.15036852845158355,0.1551578947368421,0.5797222222222222,0.5575,90.0
equities,0.5,0.2,2.0,0.7794638071771299,0.15036852845158355,0.1551578947368421,0.5797222222222222,0.5575,90.0
equities,0.5,0.4,1.0,0.4833858326082366,0.23276525976174228,0.2647368421052631,0.6397222222222222,0.6258333333333332,90.0
equities,0.5,0.4,2.0,0.9667716652164732,0.23276525976174228,0.2647368421052631,0.6397222222222222,0.6258333333333332,90.0
equities,1.2,0.0,1.0,0.314,0.0711545415170822,0.05010526315789472,0.5108333333333334,0.4913888888888889,90.0
equities,1.2,0.0,2.0,0.628,0.0711545415170822,0.05010526315789472,0.5108333333333334,0.4913888888888889,90.0
equities,1.2,0.2,1.0,0.38973190358856497,0.15036852845158355,0.1551578947368421,0.5797222222222222,0.5575,90.0
equities,1.2,0.2,2.0,0.7794638071771299,0.15036852845158355,0.1551578947368421,0.5797222222222222,0.5575,90.0
equities,1.2,0.4,1.0,0.4833858326082366,0.23276525976174228,0.2647368421052631,0.6397222222222222,0.6258333333333332,90.0
equities,1.2,0.4,2.0,0.9667716652164732,0.23276525976174228,0.2647368421052631,0.6397222222222222,0.6258333333333332,90.0
equities,2.5,0.0,1.0,0.314,0.0711545415170822,0.05010526315789472,0.5108333333333334,0.4913888888888889,90.0
equities,2.5,0.0,2.0,0.628,0.0711545415170822,0.05010526315789472,0.5108333333333334,0.4913888888888889,90.0
equities,2.5,0.2,1.0,0.38973190358856497,0.15036852845158355,0.1551578947368421,0.5797222222222222,0.5575,90.0
equities,2.5,0.2,2.0,0.7794638071771299,0.15036852845158355,0.1551578947368421,0.5797222222222222,0.5575,90.0
equities,2.5,0.4,1.0,0.4833858326082366,0.23276525976174228,0.2647368421052631,0.6397222222222222,0.6258333333333332,90.0
equities,2.5,0.4,2.0,0.9667716652164732,0.23276525976174228,0.2647368421052631,0.6397222222222222,0.6258333333333332,90.0
equities,5.0,0.0,1.0,0.314,0.0711545415170822,0.05010526315789472,0.5108333333333334,0.4913888888888889,90.0
equities,5.0,0.0,2.0,0.628,0.0711545415170822,0.05010526315789472,0.5108333333333334,0.4913888888888889,90.0
equities,5.0,0.2,1.0,0.38973190358856497,0.15036852845158355,0.1551578947368421,0.5797222222222222,0.5575,90.0
equities,5.0,0.2,2.0,0.7794638071771299,0.15036852845158355,0.1551578947368421,0.5797222222222222,0.5575,90.0
equities,5.0,0.4,1.0,0.4833858326082366,0.23276525976174228,0.2647368421052631,0.6397222222222222,0.6258333333333332,90.0
equities,5.0,0.4,2.0,0.9667716652164732,0.23276525976174228,0.2647368421052631,0.6397222222222222,0.6258333333333332,90.0
equities,8.0,0.0,1.0,0.314,0.0711545415170822,0.05010526315789472,0.5108333333333334,0.4913888888888889,90.0
equities,8.0,0.0,2.0,0.628,0.0711545415170822,0.05010526315789472,0.5108333333333334,0.4913888888888889,90.0
equities,8.0,0.2,1.0,0.38973190358856497,0.15036852845158355,0.1551578947368421,0.5797222222222222,0.5575,90.0
equities,8.0,0.2,2.0,0.7794638071771299,0.15036852845158355,0.1551578947368421,0.5797222222222222,0.5575,90.0
equities,8.0,0.4,1.0,0.4833858326082366,0.23276525976174228,0.2647368421052631,0.6397222222222222,0.6258333333333332,90.0
equities,8.0,0.4,2.0,0.9667716652164732,0.23276525976174228,0.2647368421052631,0.6397222222222222,0.6258333333333332,90.0
`,o2=`asset_class,gamma,skill,overconfidence,strategy,cagr,cagr_mean,volatility,sharpe,sharpe_p25,sharpe_p75,sortino,max_drawdown,final_multiple,effective_n,turnover,n,beat_risk_only,beat_market_hold,beat_risk_only_cagr,beat_market_hold_cagr
crypto,0.5,0.0,1.0,equal_weight,0.3015600361502324,0.2957061092325421,0.7247088031164944,0.6671626113124558,0.4436515606014521,0.8326901388307049,1.0920152205336455,-0.6799889744219247,2.2041371684032685,5.999999999999999,0.0,40,0.325,0.8,0.425,0.725
crypto,0.5,0.0,1.0,market_hold,0.15454048278050614,0.14887347181156738,0.5407569131006189,0.4647167183994304,0.09941930137308545,0.6126811083368529,0.6574025794918414,-0.6316373148964516,1.538470583910126,1.0,0.0,40,0.2,0.0,0.275,0.0
crypto,0.5,0.0,1.0,risk_only,0.3049447502506074,0.30718076988561993,0.7755090849234769,0.6787087915868288,0.46409168983019555,0.8064427904995038,1.0774265315347145,-0.7093797102938937,2.22077556439964,5.486993130387077,0.01684390937594531,40,0.0,0.8,0.0,0.725
crypto,0.5,0.0,1.0,views_calibrated_conf,0.3303655160001432,0.3224924512482198,0.8058694799359875,0.7055440700286982,0.4718197625273207,0.8275552890278675,1.1309600825402553,-0.7120367493061734,2.3532061335374297,4.180645953194803,0.2899901487615937,40,0.575,0.825,0.525,0.7
crypto,0.5,0.0,1.0,views_full_conf,0.2735910354792831,0.3037885958433516,0.7847194788741868,0.6504487978359152,0.4750360258064404,0.7882579902382774,1.0147131714129092,-0.7201772946719014,2.065163223351684,3.0388482036229743,0.4707890241848316,40,0.475,0.775,0.475,0.725
crypto,0.5,0.0,1.0,views_stated_conf,0.2828660991042683,0.3044904187053946,0.7963912103169559,0.6608518826401047,0.46739311460237715,0.8236513816337316,1.0223182303580134,-0.7156579865471058,2.112132920538703,3.1579560486027205,0.4394580377287593,40,0.475,0.75,0.475,0.725
crypto,0.5,0.0,2.0,equal_weight,0.3015600361502324,0.2957061092325421,0.7247088031164944,0.6671626113124558,0.4436515606014521,0.8326901388307049,1.0920152205336455,-0.6799889744219247,2.2041371684032685,5.999999999999999,0.0,40,0.325,0.8,0.425,0.725
crypto,0.5,0.0,2.0,market_hold,0.15454048278050614,0.14887347181156738,0.5407569131006189,0.4647167183994304,0.09941930137308545,0.6126811083368529,0.6574025794918414,-0.6316373148964516,1.538470583910126,1.0,0.0,40,0.2,0.0,0.275,0.0
crypto,0.5,0.0,2.0,risk_only,0.3049447502506074,0.30718076988561993,0.7755090849234769,0.6787087915868288,0.46409168983019555,0.8064427904995038,1.0774265315347145,-0.7093797102938937,2.22077556439964,5.486993130387077,0.01684390937594531,40,0.0,0.8,0.0,0.725
crypto,0.5,0.0,2.0,views_calibrated_conf,0.3303655160001432,0.3224924512482198,0.8058694799359875,0.7055440700286982,0.4718197625273207,0.8275552890278675,1.1309600825402553,-0.7120367493061734,2.3532061335374297,4.180645953194803,0.2899901487615937,40,0.575,0.825,0.525,0.7
crypto,0.5,0.0,2.0,views_full_conf,0.2735910354792831,0.3037885958433516,0.7847194788741868,0.6504487978359152,0.4750360258064404,0.7882579902382774,1.0147131714129092,-0.7201772946719014,2.065163223351684,3.0388482036229743,0.4707890241848316,40,0.475,0.775,0.475,0.725
crypto,0.5,0.0,2.0,views_stated_conf,0.2821254568974254,0.3098010295572315,0.7862847777209867,0.6632199394673228,0.44961947085330056,0.8740115544081823,1.0143080213936575,-0.7222640611194275,2.106348771820219,3.0719450651429776,0.45729961136208386,40,0.525,0.75,0.55,0.75
crypto,0.5,0.2,1.0,equal_weight,0.3015600361502324,0.2957061092325421,0.7247088031164944,0.6671626113124558,0.4436515606014521,0.8326901388307049,1.0920152205336455,-0.6799889744219247,2.2041371684032685,5.999999999999999,0.0,40,0.325,0.8,0.425,0.725
crypto,0.5,0.2,1.0,market_hold,0.15454048278050614,0.14887347181156738,0.5407569131006189,0.4647167183994304,0.09941930137308545,0.6126811083368529,0.6574025794918414,-0.6316373148964516,1.538470583910126,1.0,0.0,40,0.2,0.0,0.275,0.0
crypto,0.5,0.2,1.0,risk_only,0.3049447502506074,0.30718076988561993,0.7755090849234769,0.6787087915868288,0.46409168983019555,0.8064427904995038,1.0774265315347145,-0.7093797102938937,2.22077556439964,5.486993130387077,0.01684390937594531,40,0.0,0.8,0.0,0.725
crypto,0.5,0.2,1.0,views_calibrated_conf,0.3811285618250292,0.3954889084303539,0.7986394596365216,0.7523754246114683,0.5361768098435831,0.8893727099583311,1.2333589437936028,-0.7004572624985523,2.632199534940788,3.611647863497721,0.36974130195908234,40,0.75,0.825,0.725,0.8
crypto,0.5,0.2,1.0,views_full_conf,0.31527965488892196,0.39256673458139363,0.7791574086445918,0.6949576941723665,0.5471757793798052,0.8674589879722513,1.126922604728135,-0.7051604240498788,2.2742800811849944,3.033898044367704,0.46809826823095446,40,0.65,0.85,0.65,0.8
crypto,0.5,0.2,1.0,views_stated_conf,0.37557609928485725,0.41199234007294755,0.7909609814741063,0.7456847385010001,0.5739706710549223,0.9029087464243108,1.224663103186212,-0.692107667354866,2.602055546514843,3.1266654164984216,0.4411300694237264,40,0.725,0.825,0.725,0.8
crypto,0.5,0.2,2.0,equal_weight,0.3015600361502324,0.2957061092325421,0.7247088031164944,0.6671626113124558,0.4436515606014521,0.8326901388307049,1.0920152205336455,-0.6799889744219247,2.2041371684032685,5.999999999999999,0.0,40,0.325,0.8,0.425,0.725
crypto,0.5,0.2,2.0,market_hold,0.15454048278050614,0.14887347181156738,0.5407569131006189,0.4647167183994304,0.09941930137308545,0.6126811083368529,0.6574025794918414,-0.6316373148964516,1.538470583910126,1.0,0.0,40,0.2,0.0,0.275,0.0
crypto,0.5,0.2,2.0,risk_only,0.3049447502506074,0.30718076988561993,0.7755090849234769,0.6787087915868288,0.46409168983019555,0.8064427904995038,1.0774265315347145,-0.7093797102938937,2.22077556439964,5.486993130387077,0.01684390937594531,40,0.0,0.8,0.0,0.725
crypto,0.5,0.2,2.0,views_calibrated_conf,0.3811285618250292,0.3954889084303539,0.7986394596365216,0.7523754246114683,0.5361768098435831,0.8893727099583311,1.2333589437936028,-0.7004572624985523,2.632199534940788,3.611647863497721,0.36974130195908234,40,0.75,0.825,0.725,0.8
crypto,0.5,0.2,2.0,views_full_conf,0.31527965488892196,0.39256673458139363,0.7791574086445918,0.6949576941723665,0.5471757793798052,0.8674589879722513,1.126922604728135,-0.7051604240498788,2.2742800811849944,3.033898044367704,0.46809826823095446,40,0.65,0.85,0.65,0.8
crypto,0.5,0.2,2.0,views_stated_conf,0.34004261528874113,0.3980080774233847,0.7825546242683054,0.7121727633620623,0.5381128327477858,0.8713538356590991,1.1371900561446582,-0.6729918283264069,2.40501071669887,3.051060505115027,0.45482348302895326,40,0.7,0.825,0.7,0.8
crypto,0.5,0.4,1.0,equal_weight,0.3015600361502324,0.2957061092325421,0.7247088031164944,0.6671626113124558,0.4436515606014521,0.8326901388307049,1.0920152205336455,-0.6799889744219247,2.2041371684032685,5.999999999999999,0.0,40,0.325,0.8,0.425,0.725
crypto,0.5,0.4,1.0,market_hold,0.15454048278050614,0.14887347181156738,0.5407569131006189,0.4647167183994304,0.09941930137308545,0.6126811083368529,0.6574025794918414,-0.6316373148964516,1.538470583910126,1.0,0.0,40,0.2,0.0,0.275,0.0
crypto,0.5,0.4,1.0,risk_only,0.3049447502506074,0.30718076988561993,0.7755090849234769,0.6787087915868288,0.46409168983019555,0.8064427904995038,1.0774265315347145,-0.7093797102938937,2.22077556439964,5.486993130387077,0.01684390937594531,40,0.0,0.8,0.0,0.725
crypto,0.5,0.4,1.0,views_calibrated_conf,0.5043651722671642,0.5073213759562833,0.7957439513909703,0.8525847608092413,0.6168475794119693,0.9800064817017946,1.4120780069893701,-0.6735419834031661,3.400750390224167,3.324196319540431,0.3939986869332751,40,0.9,0.85,0.9,0.875
crypto,0.5,0.4,1.0,views_full_conf,0.42126125233177025,0.5067576163532491,0.7766058915980056,0.7910084847774935,0.6659103802792683,0.9702287130822722,1.2447780047818626,-0.669952822551448,2.868794443890078,3.0340557010190574,0.4441508975359546,40,0.825,0.875,0.825,0.875
crypto,0.5,0.4,1.0,views_stated_conf,0.4535839575799476,0.5235354393142881,0.7868318140998589,0.815142989033375,0.6598167242373735,0.9995663083799011,1.3369318948142088,-0.6712786190776066,3.0688378053537106,3.1000315867183015,0.4334804108489031,40,0.95,0.85,0.95,0.9
crypto,0.5,0.4,2.0,equal_weight,0.3015600361502324,0.2957061092325421,0.7247088031164944,0.6671626113124558,0.4436515606014521,0.8326901388307049,1.0920152205336455,-0.6799889744219247,2.2041371684032685,5.999999999999999,0.0,40,0.325,0.8,0.425,0.725
crypto,0.5,0.4,2.0,market_hold,0.15454048278050614,0.14887347181156738,0.5407569131006189,0.4647167183994304,0.09941930137308545,0.6126811083368529,0.6574025794918414,-0.6316373148964516,1.538470583910126,1.0,0.0,40,0.2,0.0,0.275,0.0
crypto,0.5,0.4,2.0,risk_only,0.3049447502506074,0.30718076988561993,0.7755090849234769,0.6787087915868288,0.46409168983019555,0.8064427904995038,1.0774265315347145,-0.7093797102938937,2.22077556439964,5.486993130387077,0.01684390937594531,40,0.0,0.8,0.0,0.725
crypto,0.5,0.4,2.0,views_calibrated_conf,0.5043651722671642,0.5073213759562833,0.7957439513909703,0.8525847608092413,0.6168475794119693,0.9800064817017946,1.4120780069893701,-0.6735419834031661,3.400750390224167,3.324196319540431,0.3939986869332751,40,0.9,0.85,0.9,0.875
crypto,0.5,0.4,2.0,views_full_conf,0.42126125233177025,0.5067576163532491,0.7766058915980056,0.7910084847774935,0.6659103802792683,0.9702287130822722,1.2447780047818626,-0.669952822551448,2.868794443890078,3.0340557010190574,0.4441508975359546,40,0.825,0.875,0.825,0.875
crypto,0.5,0.4,2.0,views_stated_conf,0.4236798356321675,0.5055945824525356,0.7768302321861256,0.7931022761464399,0.6632285020584451,0.9654510649042043,1.2533834242372905,-0.6663335311189472,2.8838595814193555,3.037527570294073,0.4475409345045328,40,0.825,0.875,0.85,0.9
crypto,1.2,0.0,1.0,equal_weight,0.3015600361502324,0.2957061092325421,0.7247088031164944,0.6671626113124558,0.4436515606014521,0.8326901388307049,1.0920152205336455,-0.6799889744219247,2.2041371684032685,5.999999999999999,0.0,40,0.7,0.8,0.675,0.725
crypto,1.2,0.0,1.0,market_hold,0.15454048278050614,0.14887347181156738,0.5407569131006189,0.4647167183994304,0.09941930137308545,0.6126811083368529,0.6574025794918414,-0.6316373148964516,1.538470583910126,1.0,0.0,40,0.25,0.0,0.25,0.0
crypto,1.2,0.0,1.0,risk_only,0.22326029453298768,0.23651540105696883,0.5925259993426926,0.5676110857484113,0.38148335088205976,0.8022470493040195,0.9116858716050242,-0.6055158604566012,1.8294650082510553,3.3812801580672938,0.009718049056042607,40,0.0,0.75,0.0,0.75
crypto,1.2,0.0,1.0,views_calibrated_conf,0.2800453858769353,0.2788051320110966,0.6733081198203117,0.6389622733791227,0.3811668644048568,0.8367523055847543,1.0250198538381736,-0.6436536182953346,2.0984040994996165,3.521956281393905,0.28881336028517957,40,0.525,0.75,0.475,0.725
crypto,1.2,0.0,1.0,views_full_conf,0.2412657027370454,0.297966108240994,0.7716319481033953,0.6216355302186273,0.4522241571713587,0.825542013563522,0.9639719331343299,-0.7209915217131855,1.9122825999406816,3.084510974115132,0.4692449706884154,40,0.675,0.8,0.575,0.75
crypto,1.2,0.0,1.0,views_stated_conf,0.2563105874718604,0.30342638284296874,0.7583520024338084,0.627518275564925,0.4944960976130705,0.8517237965209926,1.023742265811579,-0.693766065995111,1.9816273347253608,3.2338847660376455,0.4560636184460655,40,0.65,0.8,0.625,0.725
crypto,1.2,0.0,2.0,equal_weight,0.3015600361502324,0.2957061092325421,0.7247088031164944,0.6671626113124558,0.4436515606014521,0.8326901388307049,1.0920152205336455,-0.6799889744219247,2.2041371684032685,5.999999999999999,0.0,40,0.7,0.8,0.675,0.725
crypto,1.2,0.0,2.0,market_hold,0.15454048278050614,0.14887347181156738,0.5407569131006189,0.4647167183994304,0.09941930137308545,0.6126811083368529,0.6574025794918414,-0.6316373148964516,1.538470583910126,1.0,0.0,40,0.25,0.0,0.25,0.0
crypto,1.2,0.0,2.0,risk_only,0.22326029453298768,0.23651540105696883,0.5925259993426926,0.5676110857484113,0.38148335088205976,0.8022470493040195,0.9116858716050242,-0.6055158604566012,1.8294650082510553,3.3812801580672938,0.009718049056042607,40,0.0,0.75,0.0,0.75
crypto,1.2,0.0,2.0,views_calibrated_conf,0.2800453858769353,0.2788051320110966,0.6733081198203117,0.6389622733791227,0.3811668644048568,0.8367523055847543,1.0250198538381736,-0.6436536182953346,2.0984040994996165,3.521956281393905,0.28881336028517957,40,0.525,0.75,0.475,0.725
crypto,1.2,0.0,2.0,views_full_conf,0.2412657027370454,0.297966108240994,0.7716319481033953,0.6216355302186273,0.4522241571713587,0.825542013563522,0.9639719331343299,-0.7209915217131855,1.9122825999406816,3.084510974115132,0.4692449706884154,40,0.675,0.8,0.575,0.75
crypto,1.2,0.0,2.0,views_stated_conf,0.26226378442379406,0.3003379493213714,0.7633720086956044,0.6360405276916485,0.4506575583934625,0.8439247740919085,0.9646454355076928,-0.6866385084606267,2.0103154353123927,3.1353691967504025,0.4688692576251021,40,0.675,0.825,0.55,0.725
crypto,1.2,0.2,1.0,equal_weight,0.3015600361502324,0.2957061092325421,0.7247088031164944,0.6671626113124558,0.4436515606014521,0.8326901388307049,1.0920152205336455,-0.6799889744219247,2.2041371684032685,5.999999999999999,0.0,40,0.7,0.8,0.675,0.725
crypto,1.2,0.2,1.0,market_hold,0.15454048278050614,0.14887347181156738,0.5407569131006189,0.4647167183994304,0.09941930137308545,0.6126811083368529,0.6574025794918414,-0.6316373148964516,1.538470583910126,1.0,0.0,40,0.25,0.0,0.25,0.0
crypto,1.2,0.2,1.0,risk_only,0.22326029453298768,0.23651540105696883,0.5925259993426926,0.5676110857484113,0.38148335088205976,0.8022470493040195,0.9116858716050242,-0.6055158604566012,1.8294650082510553,3.3812801580672938,0.009718049056042607,40,0.0,0.75,0.0,0.75
crypto,1.2,0.2,1.0,views_calibrated_conf,0.35782748115979934,0.35500641942450717,0.7158900557977285,0.7333567066337985,0.4759261811799479,0.8740196330370331,1.1093576277459114,-0.6506239797408391,2.501900120538438,3.413134757252151,0.36894175517525435,40,0.725,0.8,0.725,0.8
crypto,1.2,0.2,1.0,views_full_conf,0.32762740879921004,0.39378570396350143,0.7636391352304435,0.6989987244584069,0.5263606299549455,0.8883389745748695,1.1332410228405305,-0.687429885318162,2.338257554811577,3.0864922081939907,0.4578091264387054,40,0.75,0.85,0.7,0.8
crypto,1.2,0.2,1.0,views_stated_conf,0.3735466147049491,0.4069687691284007,0.7578815450067191,0.7440733873722838,0.5488272337341209,0.9532209910185063,1.1498332912230707,-0.6705184984018964,2.5905285584881845,3.2098905344512727,0.4528035223712896,40,0.775,0.85,0.75,0.85
crypto,1.2,0.2,2.0,equal_weight,0.3015600361502324,0.2957061092325421,0.7247088031164944,0.6671626113124558,0.4436515606014521,0.8326901388307049,1.0920152205336455,-0.6799889744219247,2.2041371684032685,5.999999999999999,0.0,40,0.7,0.8,0.675,0.725
crypto,1.2,0.2,2.0,market_hold,0.15454048278050614,0.14887347181156738,0.5407569131006189,0.4647167183994304,0.09941930137308545,0.6126811083368529,0.6574025794918414,-0.6316373148964516,1.538470583910126,1.0,0.0,40,0.25,0.0,0.25,0.0
crypto,1.2,0.2,2.0,risk_only,0.22326029453298768,0.23651540105696883,0.5925259993426926,0.5676110857484113,0.38148335088205976,0.8022470493040195,0.9116858716050242,-0.6055158604566012,1.8294650082510553,3.3812801580672938,0.009718049056042607,40,0.0,0.75,0.0,0.75
crypto,1.2,0.2,2.0,views_calibrated_conf,0.35782748115979934,0.35500641942450717,0.7158900557977285,0.7333567066337985,0.4759261811799479,0.8740196330370331,1.1093576277459114,-0.6506239797408391,2.501900120538438,3.413134757252151,0.36894175517525435,40,0.725,0.8,0.725,0.8
crypto,1.2,0.2,2.0,views_full_conf,0.32762740879921004,0.39378570396350143,0.7636391352304435,0.6989987244584069,0.5263606299549455,0.8883389745748695,1.1332410228405305,-0.687429885318162,2.338257554811577,3.0864922081939907,0.4578091264387054,40,0.75,0.85,0.7,0.8
crypto,1.2,0.2,2.0,views_stated_conf,0.34605271797375725,0.4002398008107912,0.7615773087391975,0.7138931382260418,0.5306202406017355,0.9248693680388771,1.1179104665303328,-0.6642392645575008,2.4369591364419527,3.1159353385573088,0.4551865010266869,40,0.8,0.85,0.725,0.85
crypto,1.2,0.4,1.0,equal_weight,0.3015600361502324,0.2957061092325421,0.7247088031164944,0.6671626113124558,0.4436515606014521,0.8326901388307049,1.0920152205336455,-0.6799889744219247,2.2041371684032685,5.999999999999999,0.0,40,0.7,0.8,0.675,0.725
crypto,1.2,0.4,1.0,market_hold,0.15454048278050614,0.14887347181156738,0.5407569131006189,0.4647167183994304,0.09941930137308545,0.6126811083368529,0.6574025794918414,-0.6316373148964516,1.538470583910126,1.0,0.0,40,0.25,0.0,0.25,0.0
crypto,1.2,0.4,1.0,risk_only,0.22326029453298768,0.23651540105696883,0.5925259993426926,0.5676110857484113,0.38148335088205976,0.8022470493040195,0.9116858716050242,-0.6055158604566012,1.8294650082510553,3.3812801580672938,0.009718049056042607,40,0.0,0.75,0.0,0.75
crypto,1.2,0.4,1.0,views_calibrated_conf,0.48623144333485424,0.4636848887295281,0.7289014590098606,0.8558401416792851,0.5531488240776585,0.9693966917634547,1.3276465836844373,-0.6475049769905153,3.2793664343162554,3.333269583850913,0.39724076659793633,40,0.925,0.875,0.925,0.875
crypto,1.2,0.4,1.0,views_full_conf,0.46518051243198033,0.49577551420252275,0.7621211660183327,0.8314365562357853,0.6362664462574822,0.987072058876428,1.3230790668679755,-0.6662647837407233,3.150892068475148,3.0839827751416724,0.45210157885374735,40,0.925,0.875,0.95,0.9
crypto,1.2,0.4,1.0,views_stated_conf,0.4868894228149411,0.5071073995477419,0.7583676131450618,0.8421487153641551,0.6473896430223216,1.0020875968460539,1.3677655589281752,-0.6580696204737708,3.283830632640616,3.1758723029937554,0.43428783164223417,40,0.9,0.875,0.925,0.875
crypto,1.2,0.4,2.0,equal_weight,0.3015600361502324,0.2957061092325421,0.7247088031164944,0.6671626113124558,0.4436515606014521,0.8326901388307049,1.0920152205336455,-0.6799889744219247,2.2041371684032685,5.999999999999999,0.0,40,0.7,0.8,0.675,0.725
crypto,1.2,0.4,2.0,market_hold,0.15454048278050614,0.14887347181156738,0.5407569131006189,0.4647167183994304,0.09941930137308545,0.6126811083368529,0.6574025794918414,-0.6316373148964516,1.538470583910126,1.0,0.0,40,0.25,0.0,0.25,0.0
crypto,1.2,0.4,2.0,risk_only,0.22326029453298768,0.23651540105696883,0.5925259993426926,0.5676110857484113,0.38148335088205976,0.8022470493040195,0.9116858716050242,-0.6055158604566012,1.8294650082510553,3.3812801580672938,0.009718049056042607,40,0.0,0.75,0.0,0.75
crypto,1.2,0.4,2.0,views_calibrated_conf,0.48623144333485424,0.4636848887295281,0.7289014590098606,0.8558401416792851,0.5531488240776585,0.9693966917634547,1.3276465836844373,-0.6475049769905153,3.2793664343162554,3.333269583850913,0.39724076659793633,40,0.925,0.875,0.925,0.875
crypto,1.2,0.4,2.0,views_full_conf,0.46518051243198033,0.49577551420252275,0.7621211660183327,0.8314365562357853,0.6362664462574822,0.987072058876428,1.3230790668679755,-0.6662647837407233,3.150892068475148,3.0839827751416724,0.45210157885374735,40,0.925,0.875,0.95,0.9
crypto,1.2,0.4,2.0,views_stated_conf,0.463417975855847,0.49469733134313365,0.7619942144803622,0.8242558278900369,0.6325785144199638,0.9562908621146016,1.322745603890498,-0.6634366882418837,3.1409870323255835,3.092125335707694,0.45376706428729446,40,0.9,0.875,0.95,0.9
crypto,2.5,0.0,1.0,equal_weight,0.3015600361502324,0.2957061092325421,0.7247088031164944,0.6671626113124558,0.4436515606014521,0.8326901388307049,1.0920152205336455,-0.6799889744219247,2.2041371684032685,5.999999999999999,0.0,40,0.75,0.8,0.675,0.725
crypto,2.5,0.0,1.0,market_hold,0.15454048278050614,0.14887347181156738,0.5407569131006189,0.4647167183994304,0.09941930137308545,0.6126811083368529,0.6574025794918414,-0.6316373148964516,1.538470583910126,1.0,0.0,40,0.25,0.0,0.25,0.0
crypto,2.5,0.0,1.0,risk_only,0.22503013493520296,0.23256390695886,0.5909702919639598,0.5686586202297474,0.36733307644501845,0.7933548047497733,0.9069448837958646,-0.6048095243650382,1.83739607203119,3.182112297474371,0.009186257989060316,40,0.0,0.75,0.0,0.75
crypto,2.5,0.0,1.0,views_calibrated_conf,0.3107923092285323,0.26971983500518915,0.6404598499223042,0.680390006887895,0.3014665284665146,0.8602035552449889,1.0296017381772242,-0.6453296232268291,2.2505606148268633,3.29184406851044,0.16666115559012265,40,0.575,0.725,0.6,0.75
crypto,2.5,0.0,1.0,views_full_conf,0.24184043698606483,0.2959158013586962,0.7448508016841933,0.6223830115254473,0.4207055391528313,0.8355309693529717,0.9474456750110278,-0.6893646321574108,1.9143879365553302,3.1470803702296477,0.46722405720992854,40,0.625,0.8,0.55,0.7
crypto,2.5,0.0,1.0,views_stated_conf,0.2954021705290082,0.294059904925711,0.7171142991175218,0.6654371150442262,0.3970046469217631,0.826809023532356,1.0076063742885322,-0.6729616014594884,2.1723071532212948,3.302990294236384,0.41499424916566385,40,0.575,0.775,0.6,0.675
crypto,2.5,0.0,2.0,equal_weight,0.3015600361502324,0.2957061092325421,0.7247088031164944,0.6671626113124558,0.4436515606014521,0.8326901388307049,1.0920152205336455,-0.6799889744219247,2.2041371684032685,5.999999999999999,0.0,40,0.75,0.8,0.675,0.725
crypto,2.5,0.0,2.0,market_hold,0.15454048278050614,0.14887347181156738,0.5407569131006189,0.4647167183994304,0.09941930137308545,0.6126811083368529,0.6574025794918414,-0.6316373148964516,1.538470583910126,1.0,0.0,40,0.25,0.0,0.25,0.0
crypto,2.5,0.0,2.0,risk_only,0.22503013493520296,0.23256390695886,0.5909702919639598,0.5686586202297474,0.36733307644501845,0.7933548047497733,0.9069448837958646,-0.6048095243650382,1.83739607203119,3.182112297474371,0.009186257989060316,40,0.0,0.75,0.0,0.75
crypto,2.5,0.0,2.0,views_calibrated_conf,0.3107923092285323,0.26971983500518915,0.6404598499223042,0.680390006887895,0.3014665284665146,0.8602035552449889,1.0296017381772242,-0.6453296232268291,2.2505606148268633,3.29184406851044,0.16666115559012265,40,0.575,0.725,0.6,0.75
crypto,2.5,0.0,2.0,views_full_conf,0.24184043698606483,0.2959158013586962,0.7448508016841933,0.6223830115254473,0.4207055391528313,0.8355309693529717,0.9474456750110278,-0.6893646321574108,1.9143879365553302,3.1470803702296477,0.46722405720992854,40,0.625,0.8,0.55,0.7
crypto,2.5,0.0,2.0,views_stated_conf,0.26006909769190956,0.2850997921806863,0.736093536548624,0.625272315980045,0.424839009070783,0.8335780962340246,0.9351620624849498,-0.6825091462884385,2.000140668722776,3.2256162915301028,0.4536739622634603,40,0.6,0.8,0.5,0.675
crypto,2.5,0.2,1.0,equal_weight,0.3015600361502324,0.2957061092325421,0.7247088031164944,0.6671626113124558,0.4436515606014521,0.8326901388307049,1.0920152205336455,-0.6799889744219247,2.2041371684032685,5.999999999999999,0.0,40,0.75,0.8,0.675,0.725
crypto,2.5,0.2,1.0,market_hold,0.15454048278050614,0.14887347181156738,0.5407569131006189,0.4647167183994304,0.09941930137308545,0.6126811083368529,0.6574025794918414,-0.6316373148964516,1.538470583910126,1.0,0.0,40,0.25,0.0,0.25,0.0
crypto,2.5,0.2,1.0,risk_only,0.22503013493520296,0.23256390695886,0.5909702919639598,0.5686586202297474,0.36733307644501845,0.7933548047497733,0.9069448837958646,-0.6048095243650382,1.83739607203119,3.182112297474371,0.009186257989060316,40,0.0,0.75,0.0,0.75
crypto,2.5,0.2,1.0,views_calibrated_conf,0.32617137463342305,0.32576455324705683,0.6694958921487668,0.6997093761176982,0.4401498812338712,0.9114000803261578,1.0413184093442203,-0.6276647444773716,2.330971732276996,3.3075102446224003,0.30033787579320487,40,0.8,0.8,0.725,0.775
crypto,2.5,0.2,1.0,views_full_conf,0.3205929923836698,0.3767370355755765,0.7431189141659871,0.6936586784066794,0.5054727229496522,0.8974714369110282,1.104316943107296,-0.6752452449105631,2.301348798737832,3.1239510200354985,0.45809458899560074,40,0.75,0.85,0.7,0.825
crypto,2.5,0.2,1.0,views_stated_conf,0.3726511129320247,0.38798702436166704,0.7253908423238651,0.7421211609687867,0.49846468745304184,0.9360638267581116,1.1596212869956706,-0.6531661003693223,2.5840662789027116,3.276053016547345,0.4269793868743633,40,0.825,0.85,0.8,0.85
crypto,2.5,0.2,2.0,equal_weight,0.3015600361502324,0.2957061092325421,0.7247088031164944,0.6671626113124558,0.4436515606014521,0.8326901388307049,1.0920152205336455,-0.6799889744219247,2.2041371684032685,5.999999999999999,0.0,40,0.75,0.8,0.675,0.725
crypto,2.5,0.2,2.0,market_hold,0.15454048278050614,0.14887347181156738,0.5407569131006189,0.4647167183994304,0.09941930137308545,0.6126811083368529,0.6574025794918414,-0.6316373148964516,1.538470583910126,1.0,0.0,40,0.25,0.0,0.25,0.0
crypto,2.5,0.2,2.0,risk_only,0.22503013493520296,0.23256390695886,0.5909702919639598,0.5686586202297474,0.36733307644501845,0.7933548047497733,0.9069448837958646,-0.6048095243650382,1.83739607203119,3.182112297474371,0.009186257989060316,40,0.0,0.75,0.0,0.75
crypto,2.5,0.2,2.0,views_calibrated_conf,0.32617137463342305,0.32576455324705683,0.6694958921487668,0.6997093761176982,0.4401498812338712,0.9114000803261578,1.0413184093442203,-0.6276647444773716,2.330971732276996,3.3075102446224003,0.30033787579320487,40,0.8,0.8,0.725,0.775
crypto,2.5,0.2,2.0,views_full_conf,0.3205929923836698,0.3767370355755765,0.7431189141659871,0.6936586784066794,0.5054727229496522,0.8974714369110282,1.104316943107296,-0.6752452449105631,2.301348798737832,3.1239510200354985,0.45809458899560074,40,0.75,0.85,0.7,0.825
crypto,2.5,0.2,2.0,views_stated_conf,0.37451270211920706,0.3777993047264182,0.738752089959361,0.7481430909098505,0.5232976786964323,0.8929833891206722,1.159404439101397,-0.6685668562106613,2.5952846485342347,3.176187405764196,0.4526685738988559,40,0.775,0.85,0.7,0.85
crypto,2.5,0.4,1.0,equal_weight,0.3015600361502324,0.2957061092325421,0.7247088031164944,0.6671626113124558,0.4436515606014521,0.8326901388307049,1.0920152205336455,-0.6799889744219247,2.2041371684032685,5.999999999999999,0.0,40,0.75,0.8,0.675,0.725
crypto,2.5,0.4,1.0,market_hold,0.15454048278050614,0.14887347181156738,0.5407569131006189,0.4647167183994304,0.09941930137308545,0.6126811083368529,0.6574025794918414,-0.6316373148964516,1.538470583910126,1.0,0.0,40,0.25,0.0,0.25,0.0
crypto,2.5,0.4,1.0,risk_only,0.22503013493520296,0.23256390695886,0.5909702919639598,0.5686586202297474,0.36733307644501845,0.7933548047497733,0.9069448837958646,-0.6048095243650382,1.83739607203119,3.182112297474371,0.009186257989060316,40,0.0,0.75,0.0,0.75
crypto,2.5,0.4,1.0,views_calibrated_conf,0.3967204239904065,0.40792483829408654,0.690243223514946,0.7731312891088233,0.5334370567212889,0.9656405419481449,1.1946022416201996,-0.6199947056277105,2.722593719252825,3.2798594284134257,0.3589674589241748,40,0.925,0.875,0.875,0.85
crypto,2.5,0.4,1.0,views_full_conf,0.4707374927762067,0.4851687964343127,0.7392916465824253,0.839248889640172,0.6385169300587101,0.9949842687669179,1.3172980285055695,-0.6480717893168719,3.1854291870720823,3.1337004881865145,0.4455734810569394,40,0.925,0.875,0.9,0.875
crypto,2.5,0.4,1.0,views_stated_conf,0.4854900893063345,0.48256510013052567,0.7239444707137679,0.8448666884311177,0.60727935922032,1.0417947427570113,1.3268263851670015,-0.6431310837148094,3.274450313330851,3.2312316457284553,0.4166767120323434,40,0.875,0.85,0.95,0.875
crypto,2.5,0.4,2.0,equal_weight,0.3015600361502324,0.2957061092325421,0.7247088031164944,0.6671626113124558,0.4436515606014521,0.8326901388307049,1.0920152205336455,-0.6799889744219247,2.2041371684032685,5.999999999999999,0.0,40,0.75,0.8,0.675,0.725
crypto,2.5,0.4,2.0,market_hold,0.15454048278050614,0.14887347181156738,0.5407569131006189,0.4647167183994304,0.09941930137308545,0.6126811083368529,0.6574025794918414,-0.6316373148964516,1.538470583910126,1.0,0.0,40,0.25,0.0,0.25,0.0
crypto,2.5,0.4,2.0,risk_only,0.22503013493520296,0.23256390695886,0.5909702919639598,0.5686586202297474,0.36733307644501845,0.7933548047497733,0.9069448837958646,-0.6048095243650382,1.83739607203119,3.182112297474371,0.009186257989060316,40,0.0,0.75,0.0,0.75
crypto,2.5,0.4,2.0,views_calibrated_conf,0.3967204239904065,0.40792483829408654,0.690243223514946,0.7731312891088233,0.5334370567212889,0.9656405419481449,1.1946022416201996,-0.6199947056277105,2.722593719252825,3.2798594284134257,0.3589674589241748,40,0.925,0.875,0.875,0.85
crypto,2.5,0.4,2.0,views_full_conf,0.4707374927762067,0.4851687964343127,0.7392916465824253,0.839248889640172,0.6385169300587101,0.9949842687669179,1.3172980285055695,-0.6480717893168719,3.1854291870720823,3.1337004881865145,0.4455734810569394,40,0.925,0.875,0.9,0.875
crypto,2.5,0.4,2.0,views_stated_conf,0.46580249237390625,0.4864844942153425,0.7392606414574414,0.8341822494420186,0.6375834178916742,0.9957484015605921,1.3271864033677079,-0.6459120520179539,3.1526245614487403,3.1407355176799543,0.4429176274962038,40,0.925,0.875,0.925,0.875
crypto,5.0,0.0,1.0,equal_weight,0.3015600361502324,0.2957061092325421,0.7247088031164944,0.6671626113124558,0.4436515606014521,0.8326901388307049,1.0920152205336455,-0.6799889744219247,2.2041371684032685,5.999999999999999,0.0,40,0.75,0.8,0.65,0.725
crypto,5.0,0.0,1.0,market_hold,0.15454048278050614,0.14887347181156738,0.5407569131006189,0.4647167183994304,0.09941930137308545,0.6126811083368529,0.6574025794918414,-0.6316373148964516,1.538470583910126,1.0,0.0,40,0.25,0.0,0.25,0.0
crypto,5.0,0.0,1.0,risk_only,0.23165021598133573,0.23184134869402265,0.5908983042723086,0.5777747493046754,0.3637463482103996,0.7922658140161991,0.9114201841112719,-0.6045597558770084,1.8673034789801182,3.1106792545146087,0.008339654402046225,40,0.0,0.75,0.0,0.75
crypto,5.0,0.0,1.0,views_calibrated_conf,0.2701073578667951,0.2518104534713655,0.618415390669137,0.635175531694047,0.3384475687836011,0.7959230860794231,0.9996409925749523,-0.6231490554451846,2.048004180577438,3.193894002203958,0.10756517279016767,40,0.6,0.725,0.6,0.725
crypto,5.0,0.0,1.0,views_full_conf,0.26536615870569513,0.2773334040501162,0.7142494055160347,0.6281572159904109,0.4011352844668311,0.8303213085094745,0.9542058416382582,-0.6756630070710015,2.0247443934123464,3.1913934808320255,0.4378945018764998,40,0.55,0.8,0.5,0.725
crypto,5.0,0.0,1.0,views_stated_conf,0.32025398985239517,0.29226619511936036,0.6697565759130703,0.6890923127993551,0.3901062874111123,0.8099331388622921,1.0202255126262914,-0.6526142119908348,2.299560033690291,3.2713507489685245,0.3441294602223173,40,0.6,0.725,0.5,0.675
crypto,5.0,0.0,2.0,equal_weight,0.3015600361502324,0.2957061092325421,0.7247088031164944,0.6671626113124558,0.4436515606014521,0.8326901388307049,1.0920152205336455,-0.6799889744219247,2.2041371684032685,5.999999999999999,0.0,40,0.75,0.8,0.65,0.725
crypto,5.0,0.0,2.0,market_hold,0.15454048278050614,0.14887347181156738,0.5407569131006189,0.4647167183994304,0.09941930137308545,0.6126811083368529,0.6574025794918414,-0.6316373148964516,1.538470583910126,1.0,0.0,40,0.25,0.0,0.25,0.0
crypto,5.0,0.0,2.0,risk_only,0.23165021598133573,0.23184134869402265,0.5908983042723086,0.5777747493046754,0.3637463482103996,0.7922658140161991,0.9114201841112719,-0.6045597558770084,1.8673034789801182,3.1106792545146087,0.008339654402046225,40,0.0,0.75,0.0,0.75
crypto,5.0,0.0,2.0,views_calibrated_conf,0.2701073578667951,0.2518104534713655,0.618415390669137,0.635175531694047,0.3384475687836011,0.7959230860794231,0.9996409925749523,-0.6231490554451846,2.048004180577438,3.193894002203958,0.10756517279016767,40,0.6,0.725,0.6,0.725
crypto,5.0,0.0,2.0,views_full_conf,0.26536615870569513,0.2773334040501162,0.7142494055160347,0.6281572159904109,0.4011352844668311,0.8303213085094745,0.9542058416382582,-0.6756630070710015,2.0247443934123464,3.1913934808320255,0.4378945018764998,40,0.55,0.8,0.5,0.725
crypto,5.0,0.0,2.0,views_stated_conf,0.2822785131225102,0.2852656811126823,0.6971717450034036,0.6520201911068821,0.3964871784352524,0.8289879878015584,1.002364656171139,-0.6553890139468777,2.1069625152428006,3.240040230428262,0.40026870126043984,40,0.6,0.775,0.525,0.725
crypto,5.0,0.2,1.0,equal_weight,0.3015600361502324,0.2957061092325421,0.7247088031164944,0.6671626113124558,0.4436515606014521,0.8326901388307049,1.0920152205336455,-0.6799889744219247,2.2041371684032685,5.999999999999999,0.0,40,0.75,0.8,0.65,0.725
crypto,5.0,0.2,1.0,market_hold,0.15454048278050614,0.14887347181156738,0.5407569131006189,0.4647167183994304,0.09941930137308545,0.6126811083368529,0.6574025794918414,-0.6316373148964516,1.538470583910126,1.0,0.0,40,0.25,0.0,0.25,0.0
crypto,5.0,0.2,1.0,risk_only,0.23165021598133573,0.23184134869402265,0.5908983042723086,0.5777747493046754,0.3637463482103996,0.7922658140161991,0.9114201841112719,-0.6045597558770084,1.8673034789801182,3.1106792545146087,0.008339654402046225,40,0.0,0.75,0.0,0.75
crypto,5.0,0.2,1.0,views_calibrated_conf,0.34696643594750565,0.3104098662866439,0.6424336938679494,0.7220016291665391,0.4176954037536978,0.8595946039379935,1.1436503833198546,-0.6308325906572323,2.4421040669322984,3.2226378302185665,0.20950506481576117,40,0.7,0.75,0.675,0.75
crypto,5.0,0.2,1.0,views_full_conf,0.3798163654856259,0.3704401955979662,0.7163139020713507,0.746393990439221,0.4760743533037215,0.8880561241941517,1.2287272830185096,-0.660032604968521,2.6247098757736724,3.1989852681256545,0.43368008695178495,40,0.75,0.825,0.825,0.85
crypto,5.0,0.2,1.0,views_stated_conf,0.4101919262853101,0.37016638723923073,0.681163361975325,0.784171269194043,0.4754085716505212,0.8690666583683115,1.181222399158039,-0.6327580371029644,2.8017333959848645,3.2635121487983048,0.35705989846005715,40,0.8,0.8,0.725,0.8
crypto,5.0,0.2,2.0,equal_weight,0.3015600361502324,0.2957061092325421,0.7247088031164944,0.6671626113124558,0.4436515606014521,0.8326901388307049,1.0920152205336455,-0.6799889744219247,2.2041371684032685,5.999999999999999,0.0,40,0.75,0.8,0.65,0.725
crypto,5.0,0.2,2.0,market_hold,0.15454048278050614,0.14887347181156738,0.5407569131006189,0.4647167183994304,0.09941930137308545,0.6126811083368529,0.6574025794918414,-0.6316373148964516,1.538470583910126,1.0,0.0,40,0.25,0.0,0.25,0.0
crypto,5.0,0.2,2.0,risk_only,0.23165021598133573,0.23184134869402265,0.5908983042723086,0.5777747493046754,0.3637463482103996,0.7922658140161991,0.9114201841112719,-0.6045597558770084,1.8673034789801182,3.1106792545146087,0.008339654402046225,40,0.0,0.75,0.0,0.75
crypto,5.0,0.2,2.0,views_calibrated_conf,0.34696643594750565,0.3104098662866439,0.6424336938679494,0.7220016291665391,0.4176954037536978,0.8595946039379935,1.1436503833198546,-0.6308325906572323,2.4421040669322984,3.2226378302185665,0.20950506481576117,40,0.7,0.75,0.675,0.75
crypto,5.0,0.2,2.0,views_full_conf,0.3798163654856259,0.3704401955979662,0.7163139020713507,0.746393990439221,0.4760743533037215,0.8880561241941517,1.2287272830185096,-0.660032604968521,2.6247098757736724,3.1989852681256545,0.43368008695178495,40,0.75,0.825,0.825,0.85
crypto,5.0,0.2,2.0,views_stated_conf,0.38825781905591517,0.36910327678073807,0.711106288512523,0.7601145640645286,0.4791918282377565,0.9064606456024342,1.2125207138368217,-0.6494752293843239,2.6731764095604422,3.237459520250165,0.4088516863653415,40,0.8,0.825,0.8,0.85
crypto,5.0,0.4,1.0,equal_weight,0.3015600361502324,0.2957061092325421,0.7247088031164944,0.6671626113124558,0.4436515606014521,0.8326901388307049,1.0920152205336455,-0.6799889744219247,2.2041371684032685,5.999999999999999,0.0,40,0.75,0.8,0.65,0.725
crypto,5.0,0.4,1.0,market_hold,0.15454048278050614,0.14887347181156738,0.5407569131006189,0.4647167183994304,0.09941930137308545,0.6126811083368529,0.6574025794918414,-0.6316373148964516,1.538470583910126,1.0,0.0,40,0.25,0.0,0.25,0.0
crypto,5.0,0.4,1.0,risk_only,0.23165021598133573,0.23184134869402265,0.5908983042723086,0.5777747493046754,0.3637463482103996,0.7922658140161991,0.9114201841112719,-0.6045597558770084,1.8673034789801182,3.1106792545146087,0.008339654402046225,40,0.0,0.75,0.0,0.75
crypto,5.0,0.4,1.0,views_calibrated_conf,0.39347539078794624,0.375731602425218,0.6565093020797412,0.7698239181343103,0.5388247872457724,0.9142364438108522,1.2025287089388512,-0.6225461225683265,2.7037058641095726,3.2592039367293113,0.25918591721671674,40,0.825,0.875,0.775,0.875
crypto,5.0,0.4,1.0,views_full_conf,0.4823990319503816,0.47668747703262176,0.7125466777634702,0.8524337853418864,0.6435809173533688,0.9872079881206905,1.3444703663590727,-0.6164785792177847,3.254408395755926,3.188051051878382,0.41722964078154073,40,0.975,0.875,0.975,0.875
crypto,5.0,0.4,1.0,views_stated_conf,0.4335930708872786,0.44460552874993403,0.6857983961206923,0.8068505423851149,0.6036962579145666,0.9863895868542003,1.291719199390216,-0.6177291511660659,2.9439580515859807,3.252299197473202,0.36685589481875625,40,0.9,0.85,0.975,0.875
crypto,5.0,0.4,2.0,equal_weight,0.3015600361502324,0.2957061092325421,0.7247088031164944,0.6671626113124558,0.4436515606014521,0.8326901388307049,1.0920152205336455,-0.6799889744219247,2.2041371684032685,5.999999999999999,0.0,40,0.75,0.8,0.65,0.725
crypto,5.0,0.4,2.0,market_hold,0.15454048278050614,0.14887347181156738,0.5407569131006189,0.4647167183994304,0.09941930137308545,0.6126811083368529,0.6574025794918414,-0.6316373148964516,1.538470583910126,1.0,0.0,40,0.25,0.0,0.25,0.0
crypto,5.0,0.4,2.0,risk_only,0.23165021598133573,0.23184134869402265,0.5908983042723086,0.5777747493046754,0.3637463482103996,0.7922658140161991,0.9114201841112719,-0.6045597558770084,1.8673034789801182,3.1106792545146087,0.008339654402046225,40,0.0,0.75,0.0,0.75
crypto,5.0,0.4,2.0,views_calibrated_conf,0.39347539078794624,0.375731602425218,0.6565093020797412,0.7698239181343103,0.5388247872457724,0.9142364438108522,1.2025287089388512,-0.6225461225683265,2.7037058641095726,3.2592039367293113,0.25918591721671674,40,0.825,0.875,0.775,0.875
crypto,5.0,0.4,2.0,views_full_conf,0.4823990319503816,0.47668747703262176,0.7125466777634702,0.8524337853418864,0.6435809173533688,0.9872079881206905,1.3444703663590727,-0.6164785792177847,3.254408395755926,3.188051051878382,0.41722964078154073,40,0.975,0.875,0.975,0.875
crypto,5.0,0.4,2.0,views_stated_conf,0.4858784955253288,0.4752770187244191,0.7107393009670948,0.8575764104729826,0.6438724482314611,0.988172574707748,1.337504518397817,-0.6160352536938485,3.279312047782734,3.2040479271800795,0.41573093168666886,40,1.0,0.875,1.0,0.875
crypto,8.0,0.0,1.0,equal_weight,0.3015600361502324,0.2957061092325421,0.7247088031164944,0.6671626113124558,0.4436515606014521,0.8326901388307049,1.0920152205336455,-0.6799889744219247,2.2041371684032685,5.999999999999999,0.0,40,0.725,0.8,0.65,0.725
crypto,8.0,0.0,1.0,market_hold,0.15454048278050614,0.14887347181156738,0.5407569131006189,0.4647167183994304,0.09941930137308545,0.6126811083368529,0.6574025794918414,-0.6316373148964516,1.538470583910126,1.0,0.0,40,0.25,0.0,0.25,0.0
crypto,8.0,0.0,1.0,risk_only,0.23312353619186688,0.23171206759123505,0.5909190387640023,0.5797993685833593,0.36311209763683927,0.7907221210770671,0.9131132749163564,-0.6043078760552039,1.8740136576812227,3.090256125913844,0.00788225978243573,40,0.0,0.75,0.0,0.75
crypto,8.0,0.0,1.0,views_calibrated_conf,0.23961816941679348,0.240706410932868,0.6055913631348916,0.5934892955644188,0.35978304239663483,0.7747337172466815,0.9761872483568379,-0.6322626076089268,1.903908212615348,3.148937665086307,0.07529892640560526,40,0.6,0.75,0.575,0.75
crypto,8.0,0.0,1.0,views_full_conf,0.28066937254686397,0.28265086082858193,0.68997500806393,0.6421292270481008,0.38038548538942085,0.8033920215306091,0.9722890277641001,-0.6607294641319839,2.0990689116242436,3.204508638017292,0.401757677654545,40,0.575,0.725,0.475,0.7
crypto,8.0,0.0,1.0,views_stated_conf,0.29368213056016623,0.28561748827138494,0.6524906554682678,0.6581387989367438,0.39373778338042653,0.8131845815988396,1.029820911702704,-0.6369890741946234,2.1636144393962837,3.238530930301684,0.2795118544715911,40,0.525,0.675,0.55,0.675
crypto,8.0,0.0,2.0,equal_weight,0.3015600361502324,0.2957061092325421,0.7247088031164944,0.6671626113124558,0.4436515606014521,0.8326901388307049,1.0920152205336455,-0.6799889744219247,2.2041371684032685,5.999999999999999,0.0,40,0.725,0.8,0.65,0.725
crypto,8.0,0.0,2.0,market_hold,0.15454048278050614,0.14887347181156738,0.5407569131006189,0.4647167183994304,0.09941930137308545,0.6126811083368529,0.6574025794918414,-0.6316373148964516,1.538470583910126,1.0,0.0,40,0.25,0.0,0.25,0.0
crypto,8.0,0.0,2.0,risk_only,0.23312353619186688,0.23171206759123505,0.5909190387640023,0.5797993685833593,0.36311209763683927,0.7907221210770671,0.9131132749163564,-0.6043078760552039,1.8740136576812227,3.090256125913844,0.00788225978243573,40,0.0,0.75,0.0,0.75
crypto,8.0,0.0,2.0,views_calibrated_conf,0.23961816941679348,0.240706410932868,0.6055913631348916,0.5934892955644188,0.35978304239663483,0.7747337172466815,0.9761872483568379,-0.6322626076089268,1.903908212615348,3.148937665086307,0.07529892640560526,40,0.6,0.75,0.575,0.75
crypto,8.0,0.0,2.0,views_full_conf,0.28066937254686397,0.28265086082858193,0.68997500806393,0.6421292270481008,0.38038548538942085,0.8033920215306091,0.9722890277641001,-0.6607294641319839,2.0990689116242436,3.204508638017292,0.401757677654545,40,0.575,0.725,0.475,0.7
crypto,8.0,0.0,2.0,views_stated_conf,0.2922673800221175,0.28257233522459113,0.6725474691153219,0.6574131287125904,0.38495014610352923,0.790169306106661,1.0102292709881002,-0.6514677679046441,2.156972707606239,3.231445380859502,0.35232884848738666,40,0.625,0.75,0.525,0.65
crypto,8.0,0.2,1.0,equal_weight,0.3015600361502324,0.2957061092325421,0.7247088031164944,0.6671626113124558,0.4436515606014521,0.8326901388307049,1.0920152205336455,-0.6799889744219247,2.2041371684032685,5.999999999999999,0.0,40,0.725,0.8,0.65,0.725
crypto,8.0,0.2,1.0,market_hold,0.15454048278050614,0.14887347181156738,0.5407569131006189,0.4647167183994304,0.09941930137308545,0.6126811083368529,0.6574025794918414,-0.6316373148964516,1.538470583910126,1.0,0.0,40,0.25,0.0,0.25,0.0
crypto,8.0,0.2,1.0,risk_only,0.23312353619186688,0.23171206759123505,0.5909190387640023,0.5797993685833593,0.36311209763683927,0.7907221210770671,0.9131132749163564,-0.6043078760552039,1.8740136576812227,3.090256125913844,0.00788225978243573,40,0.0,0.75,0.0,0.75
crypto,8.0,0.2,1.0,views_calibrated_conf,0.3453566111227323,0.28886304777884086,0.6250951859668893,0.7178380643907971,0.3900550561692977,0.8196276714011649,1.1503885565533891,-0.631701499762743,2.433123200524455,3.1829897007993764,0.1593247453133036,40,0.675,0.75,0.7,0.75
crypto,8.0,0.2,1.0,views_full_conf,0.37387402060015673,0.36623419905102345,0.6923762427729041,0.7509620905257839,0.4866490173150339,0.9112894293057633,1.1527744770125248,-0.6508962719836273,2.5911097653706747,3.2027395170981565,0.39624547331617305,40,0.775,0.825,0.775,0.8
crypto,8.0,0.2,1.0,views_stated_conf,0.3640808942406891,0.35132535038508894,0.6530515305169724,0.7398648243066639,0.4800164059808572,0.8821357662395662,1.1598067377192764,-0.6162781072437862,2.5360121171048133,3.230341398244919,0.29348459138595284,40,0.825,0.775,0.825,0.75
crypto,8.0,0.2,2.0,equal_weight,0.3015600361502324,0.2957061092325421,0.7247088031164944,0.6671626113124558,0.4436515606014521,0.8326901388307049,1.0920152205336455,-0.6799889744219247,2.2041371684032685,5.999999999999999,0.0,40,0.725,0.8,0.65,0.725
crypto,8.0,0.2,2.0,market_hold,0.15454048278050614,0.14887347181156738,0.5407569131006189,0.4647167183994304,0.09941930137308545,0.6126811083368529,0.6574025794918414,-0.6316373148964516,1.538470583910126,1.0,0.0,40,0.25,0.0,0.25,0.0
crypto,8.0,0.2,2.0,risk_only,0.23312353619186688,0.23171206759123505,0.5909190387640023,0.5797993685833593,0.36311209763683927,0.7907221210770671,0.9131132749163564,-0.6043078760552039,1.8740136576812227,3.090256125913844,0.00788225978243573,40,0.0,0.75,0.0,0.75
crypto,8.0,0.2,2.0,views_calibrated_conf,0.3453566111227323,0.28886304777884086,0.6250951859668893,0.7178380643907971,0.3900550561692977,0.8196276714011649,1.1503885565533891,-0.631701499762743,2.433123200524455,3.1829897007993764,0.1593247453133036,40,0.675,0.75,0.7,0.75
crypto,8.0,0.2,2.0,views_full_conf,0.37387402060015673,0.36623419905102345,0.6923762427729041,0.7509620905257839,0.4866490173150339,0.9112894293057633,1.1527744770125248,-0.6508962719836273,2.5911097653706747,3.2027395170981565,0.39624547331617305,40,0.775,0.825,0.775,0.8
crypto,8.0,0.2,2.0,views_stated_conf,0.38384343883325267,0.36842079844519826,0.6828855263298501,0.752427605748692,0.4647052610145018,0.8999871035156857,1.1657578484929847,-0.6395314075985077,2.6477345776206143,3.2225311231021756,0.3669168841397781,40,0.775,0.825,0.775,0.825
crypto,8.0,0.4,1.0,equal_weight,0.3015600361502324,0.2957061092325421,0.7247088031164944,0.6671626113124558,0.4436515606014521,0.8326901388307049,1.0920152205336455,-0.6799889744219247,2.2041371684032685,5.999999999999999,0.0,40,0.725,0.8,0.65,0.725
crypto,8.0,0.4,1.0,market_hold,0.15454048278050614,0.14887347181156738,0.5407569131006189,0.4647167183994304,0.09941930137308545,0.6126811083368529,0.6574025794918414,-0.6316373148964516,1.538470583910126,1.0,0.0,40,0.25,0.0,0.25,0.0
crypto,8.0,0.4,1.0,risk_only,0.23312353619186688,0.23171206759123505,0.5909190387640023,0.5797993685833593,0.36311209763683927,0.7907221210770671,0.9131132749163564,-0.6043078760552039,1.8740136576812227,3.090256125913844,0.00788225978243573,40,0.0,0.75,0.0,0.75
crypto,8.0,0.4,1.0,views_calibrated_conf,0.4072776394179395,0.3471285704344312,0.6421032032805056,0.7863885621420686,0.4936729769209197,0.8876781726872851,1.228677358904922,-0.6160430308018726,2.784857309177898,3.205022187034772,0.2050084156556789,40,0.825,0.8,0.775,0.825
crypto,8.0,0.4,1.0,views_full_conf,0.4643742851726109,0.4562962210126348,0.6861049269378303,0.8424008655894966,0.5796424602194976,0.9745714872045281,1.3201879199521458,-0.6128104229840832,3.1369762256873264,3.196536519175731,0.3794003234660887,40,0.925,0.85,0.95,0.9
crypto,8.0,0.4,1.0,views_stated_conf,0.42867358574788283,0.4215753232989595,0.6641947346728289,0.801358642733712,0.582796367789822,0.9722666115656233,1.217216940266355,-0.6144805753186964,2.9132561612781727,3.242282823832316,0.29855077121146084,40,0.95,0.85,0.975,0.9
crypto,8.0,0.4,2.0,equal_weight,0.3015600361502324,0.2957061092325421,0.7247088031164944,0.6671626113124558,0.4436515606014521,0.8326901388307049,1.0920152205336455,-0.6799889744219247,2.2041371684032685,5.999999999999999,0.0,40,0.725,0.8,0.65,0.725
crypto,8.0,0.4,2.0,market_hold,0.15454048278050614,0.14887347181156738,0.5407569131006189,0.4647167183994304,0.09941930137308545,0.6126811083368529,0.6574025794918414,-0.6316373148964516,1.538470583910126,1.0,0.0,40,0.25,0.0,0.25,0.0
crypto,8.0,0.4,2.0,risk_only,0.23312353619186688,0.23171206759123505,0.5909190387640023,0.5797993685833593,0.36311209763683927,0.7907221210770671,0.9131132749163564,-0.6043078760552039,1.8740136576812227,3.090256125913844,0.00788225978243573,40,0.0,0.75,0.0,0.75
crypto,8.0,0.4,2.0,views_calibrated_conf,0.4072776394179395,0.3471285704344312,0.6421032032805056,0.7863885621420686,0.4936729769209197,0.8876781726872851,1.228677358904922,-0.6160430308018726,2.784857309177898,3.205022187034772,0.2050084156556789,40,0.825,0.8,0.775,0.825
crypto,8.0,0.4,2.0,views_full_conf,0.4643742851726109,0.4562962210126348,0.6861049269378303,0.8424008655894966,0.5796424602194976,0.9745714872045281,1.3201879199521458,-0.6128104229840832,3.1369762256873264,3.196536519175731,0.3794003234660887,40,0.925,0.85,0.95,0.9
crypto,8.0,0.4,2.0,views_stated_conf,0.46775215358523314,0.4545858585928576,0.6846940774969812,0.8463133169266738,0.5849483909017095,0.9744881751458256,1.3144647245547874,-0.6127931451190948,3.1589494777031177,3.2020539624502113,0.37756193954416695,40,0.925,0.85,0.975,0.9
`,a2=`asset_class,gamma,skill,overconfidence,strategy,cagr,cagr_mean,volatility,sharpe,sharpe_p25,sharpe_p75,sortino,max_drawdown,final_multiple,effective_n,turnover,n,beat_risk_only,beat_market_hold,beat_risk_only_cagr,beat_market_hold_cagr
equities,0.5,0.0,1.0,equal_weight,0.12341059365887486,0.12675011450781187,0.2256558477961915,0.46851391738540443,0.3248717034062219,0.642302409312645,0.784591379980037,-0.2855686051005571,1.5920383947690195,5.999999999999999,0.0,40,0.65,0.7,0.375,0.6
equities,0.5,0.0,1.0,market_hold,0.12306716854170785,0.1049495198569231,0.3366874814448674,0.42907420899583437,0.22398392939148923,0.5363240853411446,0.7176054294318316,-0.4283798073581172,1.5901201847861306,1.0,0.0,40,0.425,0.0,0.45,0.0
equities,0.5,0.0,1.0,risk_only,0.14623108783541816,0.1301564876880053,0.28967022274207493,0.46842038986336665,0.238040119142372,0.5958664070602046,0.8030814711359116,-0.3944980183102699,1.7252784376131274,3.1718582918757043,0.02622308178099971,40,0.0,0.575,0.0,0.55
equities,0.5,0.0,1.0,views_calibrated_conf,0.12178252214711272,0.12358582632938384,0.28744943284372165,0.40878830961918716,0.2067550202449893,0.6117074272963743,0.6958661881010113,-0.3907879031643372,1.582862318515196,3.1682683448395395,0.1661899182886231,40,0.475,0.575,0.45,0.6
equities,0.5,0.0,1.0,views_full_conf,0.11828166704344556,0.11162633688351717,0.25858216592993033,0.4057385628447975,0.15816625200137407,0.5481940624920912,0.679530221051257,-0.3634997820878953,1.5633401803758122,3.0488723112420932,0.47475835999671334,40,0.4,0.525,0.375,0.575
equities,0.5,0.0,1.0,views_stated_conf,0.12401433402432482,0.1169522397886011,0.2675274805746185,0.4206507914921872,0.23027962024255022,0.5980040722456735,0.7154059714241777,-0.37499904067188233,1.5955576859889495,3.163036975741599,0.4064423951481886,40,0.475,0.575,0.45,0.55
equities,0.5,0.0,2.0,equal_weight,0.12341059365887486,0.12675011450781187,0.2256558477961915,0.46851391738540443,0.3248717034062219,0.642302409312645,0.784591379980037,-0.2855686051005571,1.5920383947690195,5.999999999999999,0.0,40,0.65,0.7,0.375,0.6
equities,0.5,0.0,2.0,market_hold,0.12306716854170785,0.1049495198569231,0.3366874814448674,0.42907420899583437,0.22398392939148923,0.5363240853411446,0.7176054294318316,-0.4283798073581172,1.5901201847861306,1.0,0.0,40,0.425,0.0,0.45,0.0
equities,0.5,0.0,2.0,risk_only,0.14623108783541816,0.1301564876880053,0.28967022274207493,0.46842038986336665,0.238040119142372,0.5958664070602046,0.8030814711359116,-0.3944980183102699,1.7252784376131274,3.1718582918757043,0.02622308178099971,40,0.0,0.575,0.0,0.55
equities,0.5,0.0,2.0,views_calibrated_conf,0.12178252214711272,0.12358582632938384,0.28744943284372165,0.40878830961918716,0.2067550202449893,0.6117074272963743,0.6958661881010113,-0.3907879031643372,1.582862318515196,3.1682683448395395,0.1661899182886231,40,0.475,0.575,0.45,0.6
equities,0.5,0.0,2.0,views_full_conf,0.11828166704344556,0.11162633688351717,0.25858216592993033,0.4057385628447975,0.15816625200137407,0.5481940624920912,0.679530221051257,-0.3634997820878953,1.5633401803758122,3.0488723112420932,0.47475835999671334,40,0.4,0.525,0.375,0.575
equities,0.5,0.0,2.0,views_stated_conf,0.11095008243806825,0.10939773736334057,0.2598077027814655,0.37599142235322736,0.16519680210306514,0.5392288720616365,0.636962538225111,-0.37380189225984894,1.5226447291174126,3.082782990582705,0.4544953713788008,40,0.4,0.55,0.425,0.55
equities,0.5,0.2,1.0,equal_weight,0.12341059365887486,0.12675011450781187,0.2256558477961915,0.46851391738540443,0.3248717034062219,0.642302409312645,0.784591379980037,-0.2855686051005571,1.5920383947690195,5.999999999999999,0.0,40,0.65,0.7,0.375,0.6
equities,0.5,0.2,1.0,market_hold,0.12306716854170785,0.1049495198569231,0.3366874814448674,0.42907420899583437,0.22398392939148923,0.5363240853411446,0.7176054294318316,-0.4283798073581172,1.5901201847861306,1.0,0.0,40,0.425,0.0,0.45,0.0
equities,0.5,0.2,1.0,risk_only,0.14623108783541816,0.1301564876880053,0.28967022274207493,0.46842038986336665,0.238040119142372,0.5958664070602046,0.8030814711359116,-0.3944980183102699,1.7252784376131274,3.1718582918757043,0.02622308178099971,40,0.0,0.575,0.0,0.55
equities,0.5,0.2,1.0,views_calibrated_conf,0.14174370229528122,0.13676522803399224,0.2801755747169123,0.45912623623051385,0.2996008817552164,0.6171621679886193,0.7617021183647917,-0.37904537420221374,1.6985596154744713,3.1648578378125425,0.27258069601493085,40,0.675,0.65,0.675,0.675
equities,0.5,0.2,1.0,views_full_conf,0.12009732887582192,0.13536993546848022,0.25633564555347244,0.4061506670069778,0.24614267319159325,0.655317630871182,0.6832755283664051,-0.3460131717142554,1.5734067723066882,3.045003438873139,0.4677044196236708,40,0.55,0.65,0.575,0.575
equities,0.5,0.2,1.0,views_stated_conf,0.148012944783813,0.14173210508132716,0.26384401787367195,0.5082721487481696,0.3301595074349572,0.6479641984038076,0.8554582371106927,-0.34359165461508334,1.7360036484098802,3.1416415294371243,0.41687196559232204,40,0.6,0.725,0.55,0.7
equities,0.5,0.2,2.0,equal_weight,0.12341059365887486,0.12675011450781187,0.2256558477961915,0.46851391738540443,0.3248717034062219,0.642302409312645,0.784591379980037,-0.2855686051005571,1.5920383947690195,5.999999999999999,0.0,40,0.65,0.7,0.375,0.6
equities,0.5,0.2,2.0,market_hold,0.12306716854170785,0.1049495198569231,0.3366874814448674,0.42907420899583437,0.22398392939148923,0.5363240853411446,0.7176054294318316,-0.4283798073581172,1.5901201847861306,1.0,0.0,40,0.425,0.0,0.45,0.0
equities,0.5,0.2,2.0,risk_only,0.14623108783541816,0.1301564876880053,0.28967022274207493,0.46842038986336665,0.238040119142372,0.5958664070602046,0.8030814711359116,-0.3944980183102699,1.7252784376131274,3.1718582918757043,0.02622308178099971,40,0.0,0.575,0.0,0.55
equities,0.5,0.2,2.0,views_calibrated_conf,0.14174370229528122,0.13676522803399224,0.2801755747169123,0.45912623623051385,0.2996008817552164,0.6171621679886193,0.7617021183647917,-0.37904537420221374,1.6985596154744713,3.1648578378125425,0.27258069601493085,40,0.675,0.65,0.675,0.675
equities,0.5,0.2,2.0,views_full_conf,0.12009732887582192,0.13536993546848022,0.25633564555347244,0.4061506670069778,0.24614267319159325,0.655317630871182,0.6832755283664051,-0.3460131717142554,1.5734067723066882,3.045003438873139,0.4677044196236708,40,0.55,0.65,0.575,0.575
equities,0.5,0.2,2.0,views_stated_conf,0.11828389403339301,0.13754607317251824,0.2576731118357677,0.40317818492379465,0.3048367373854161,0.636161790130991,0.674317737796504,-0.35361920063110097,1.5632171247406004,3.0646124947199294,0.46315223787188586,40,0.575,0.675,0.525,0.65
equities,0.5,0.4,1.0,equal_weight,0.12341059365887486,0.12675011450781187,0.2256558477961915,0.46851391738540443,0.3248717034062219,0.642302409312645,0.784591379980037,-0.2855686051005571,1.5920383947690195,5.999999999999999,0.0,40,0.65,0.7,0.375,0.6
equities,0.5,0.4,1.0,market_hold,0.12306716854170785,0.1049495198569231,0.3366874814448674,0.42907420899583437,0.22398392939148923,0.5363240853411446,0.7176054294318316,-0.4283798073581172,1.5901201847861306,1.0,0.0,40,0.425,0.0,0.45,0.0
equities,0.5,0.4,1.0,risk_only,0.14623108783541816,0.1301564876880053,0.28967022274207493,0.46842038986336665,0.238040119142372,0.5958664070602046,0.8030814711359116,-0.3944980183102699,1.7252784376131274,3.1718582918757043,0.02622308178099971,40,0.0,0.575,0.0,0.55
equities,0.5,0.4,1.0,views_calibrated_conf,0.15215299719070285,0.1585858616967217,0.2727387083627631,0.544995646335964,0.40216160489891006,0.6678137324893116,0.9429303596983861,-0.3513094716854789,1.7612161652404743,3.1642314413676322,0.326641024607028,40,0.775,0.75,0.725,0.725
equities,0.5,0.4,1.0,views_full_conf,0.16875061528685242,0.16746259354685006,0.25635381819534153,0.5570609074980529,0.37749090494766846,0.7374977299248616,0.9376115989029438,-0.33144679432386975,1.8647424597885722,3.045099891870111,0.4675084324641087,40,0.8,0.8,0.8,0.8
equities,0.5,0.4,1.0,views_stated_conf,0.16233524676376931,0.16614527048720332,0.2603167934636894,0.5480613230682598,0.41606990192726606,0.766667168406011,0.9250945436264624,-0.33469908464186593,1.8242428603422063,3.114001407245989,0.44272924677037917,40,0.8,0.825,0.725,0.8
equities,0.5,0.4,2.0,equal_weight,0.12341059365887486,0.12675011450781187,0.2256558477961915,0.46851391738540443,0.3248717034062219,0.642302409312645,0.784591379980037,-0.2855686051005571,1.5920383947690195,5.999999999999999,0.0,40,0.65,0.7,0.375,0.6
equities,0.5,0.4,2.0,market_hold,0.12306716854170785,0.1049495198569231,0.3366874814448674,0.42907420899583437,0.22398392939148923,0.5363240853411446,0.7176054294318316,-0.4283798073581172,1.5901201847861306,1.0,0.0,40,0.425,0.0,0.45,0.0
equities,0.5,0.4,2.0,risk_only,0.14623108783541816,0.1301564876880053,0.28967022274207493,0.46842038986336665,0.238040119142372,0.5958664070602046,0.8030814711359116,-0.3944980183102699,1.7252784376131274,3.1718582918757043,0.02622308178099971,40,0.0,0.575,0.0,0.55
equities,0.5,0.4,2.0,views_calibrated_conf,0.15215299719070285,0.1585858616967217,0.2727387083627631,0.544995646335964,0.40216160489891006,0.6678137324893116,0.9429303596983861,-0.3513094716854789,1.7612161652404743,3.1642314413676322,0.326641024607028,40,0.775,0.75,0.725,0.725
equities,0.5,0.4,2.0,views_full_conf,0.16875061528685242,0.16746259354685006,0.25635381819534153,0.5570609074980529,0.37749090494766846,0.7374977299248616,0.9376115989029438,-0.33144679432386975,1.8647424597885722,3.045099891870111,0.4675084324641087,40,0.8,0.8,0.8,0.8
equities,0.5,0.4,2.0,views_stated_conf,0.16750226291396075,0.16723141476382392,0.25661202006825634,0.5546959630163806,0.376411119242958,0.728718645942968,0.9226878217975216,-0.33097660584123356,1.8568057477402673,3.0458417928266464,0.46677497158911874,40,0.8,0.8,0.8,0.775
equities,1.2,0.0,1.0,equal_weight,0.12341059365887486,0.12675011450781187,0.2256558477961915,0.46851391738540443,0.3248717034062219,0.642302409312645,0.784591379980037,-0.2855686051005571,1.5920383947690195,5.999999999999999,0.0,40,0.625,0.7,0.425,0.6
equities,1.2,0.0,1.0,market_hold,0.12306716854170785,0.1049495198569231,0.3366874814448674,0.42907420899583437,0.22398392939148923,0.5363240853411446,0.7176054294318316,-0.4283798073581172,1.5901201847861306,1.0,0.0,40,0.35,0.0,0.375,0.0
equities,1.2,0.0,1.0,risk_only,0.13477479333092202,0.1286509297403245,0.26670308279795807,0.44979510366716813,0.2695294930919465,0.6399254587037934,0.7516994286408649,-0.3696834808299144,1.6575375820884322,4.293553439665313,0.017947018026381822,40,0.0,0.65,0.0,0.625
equities,1.2,0.0,1.0,views_calibrated_conf,0.1049084827304575,0.12091863259229998,0.2620881138957546,0.38246002929126566,0.25726818213938146,0.5808244317688904,0.6590236085726529,-0.362072499367357,1.489840778502366,4.134311721329712,0.22646627721381035,40,0.325,0.525,0.3,0.55
equities,1.2,0.0,1.0,views_full_conf,0.127065806796689,0.11686492026437914,0.2531835822154345,0.4352317016600703,0.21034930566646842,0.5527401814077028,0.7190405324288344,-0.3402320932598053,1.6130373118566297,3.1385158213325246,0.4748162993150683,40,0.45,0.575,0.4,0.55
equities,1.2,0.0,1.0,views_stated_conf,0.11751456068831578,0.11769572621180069,0.25312980157706705,0.4105641533283706,0.2381211999970944,0.5568270155996072,0.697709353793377,-0.35318938259528265,1.5589110076778279,3.437854085790966,0.43225499352094265,40,0.4,0.6,0.4,0.6
equities,1.2,0.0,2.0,equal_weight,0.12341059365887486,0.12675011450781187,0.2256558477961915,0.46851391738540443,0.3248717034062219,0.642302409312645,0.784591379980037,-0.2855686051005571,1.5920383947690195,5.999999999999999,0.0,40,0.625,0.7,0.425,0.6
equities,1.2,0.0,2.0,market_hold,0.12306716854170785,0.1049495198569231,0.3366874814448674,0.42907420899583437,0.22398392939148923,0.5363240853411446,0.7176054294318316,-0.4283798073581172,1.5901201847861306,1.0,0.0,40,0.35,0.0,0.375,0.0
equities,1.2,0.0,2.0,risk_only,0.13477479333092202,0.1286509297403245,0.26670308279795807,0.44979510366716813,0.2695294930919465,0.6399254587037934,0.7516994286408649,-0.3696834808299144,1.6575375820884322,4.293553439665313,0.017947018026381822,40,0.0,0.65,0.0,0.625
equities,1.2,0.0,2.0,views_calibrated_conf,0.1049084827304575,0.12091863259229998,0.2620881138957546,0.38246002929126566,0.25726818213938146,0.5808244317688904,0.6590236085726529,-0.362072499367357,1.489840778502366,4.134311721329712,0.22646627721381035,40,0.325,0.525,0.3,0.55
equities,1.2,0.0,2.0,views_full_conf,0.127065806796689,0.11686492026437914,0.2531835822154345,0.4352317016600703,0.21034930566646842,0.5527401814077028,0.7190405324288344,-0.3402320932598053,1.6130373118566297,3.1385158213325246,0.4748162993150683,40,0.45,0.575,0.4,0.55
equities,1.2,0.0,2.0,views_stated_conf,0.11679196036276995,0.11560338239622267,0.25371943748270237,0.4058316708944445,0.20694863864849442,0.5301247417777479,0.662927143860639,-0.3564434496305851,1.5549221460129,3.2449028352205858,0.46085846956229826,40,0.4,0.625,0.375,0.55
equities,1.2,0.2,1.0,equal_weight,0.12341059365887486,0.12675011450781187,0.2256558477961915,0.46851391738540443,0.3248717034062219,0.642302409312645,0.784591379980037,-0.2855686051005571,1.5920383947690195,5.999999999999999,0.0,40,0.625,0.7,0.425,0.6
equities,1.2,0.2,1.0,market_hold,0.12306716854170785,0.1049495198569231,0.3366874814448674,0.42907420899583437,0.22398392939148923,0.5363240853411446,0.7176054294318316,-0.4283798073581172,1.5901201847861306,1.0,0.0,40,0.35,0.0,0.375,0.0
equities,1.2,0.2,1.0,risk_only,0.13477479333092202,0.1286509297403245,0.26670308279795807,0.44979510366716813,0.2695294930919465,0.6399254587037934,0.7516994286408649,-0.3696834808299144,1.6575375820884322,4.293553439665313,0.017947018026381822,40,0.0,0.65,0.0,0.625
equities,1.2,0.2,1.0,views_calibrated_conf,0.14769604921234147,0.14076242417308854,0.2601958153157665,0.5018219536010772,0.2986441127277737,0.5880142382079487,0.8509695091019127,-0.3406399045711713,1.734128948818767,3.7974371264409497,0.33389192851356975,40,0.675,0.725,0.65,0.7
equities,1.2,0.2,1.0,views_full_conf,0.1208358090685211,0.1388148669631386,0.2520468478715272,0.4274519380538496,0.2809864122504722,0.6562121951380189,0.7043314230261237,-0.32766221473726487,1.5775354328201663,3.1438323088310356,0.468223850876543,40,0.625,0.675,0.625,0.625
equities,1.2,0.2,1.0,views_stated_conf,0.13182398882430058,0.14321179891097202,0.2538736306416687,0.4746933062848938,0.31952487088432313,0.6298846708713242,0.7907592040596981,-0.33227058131135445,1.6402863530159486,3.3652195927767177,0.4344271963266303,40,0.625,0.675,0.6,0.675
equities,1.2,0.2,2.0,equal_weight,0.12341059365887486,0.12675011450781187,0.2256558477961915,0.46851391738540443,0.3248717034062219,0.642302409312645,0.784591379980037,-0.2855686051005571,1.5920383947690195,5.999999999999999,0.0,40,0.625,0.7,0.425,0.6
equities,1.2,0.2,2.0,market_hold,0.12306716854170785,0.1049495198569231,0.3366874814448674,0.42907420899583437,0.22398392939148923,0.5363240853411446,0.7176054294318316,-0.4283798073581172,1.5901201847861306,1.0,0.0,40,0.35,0.0,0.375,0.0
equities,1.2,0.2,2.0,risk_only,0.13477479333092202,0.1286509297403245,0.26670308279795807,0.44979510366716813,0.2695294930919465,0.6399254587037934,0.7516994286408649,-0.3696834808299144,1.6575375820884322,4.293553439665313,0.017947018026381822,40,0.0,0.65,0.0,0.625
equities,1.2,0.2,2.0,views_calibrated_conf,0.14769604921234147,0.14076242417308854,0.2601958153157665,0.5018219536010772,0.2986441127277737,0.5880142382079487,0.8509695091019127,-0.3406399045711713,1.734128948818767,3.7974371264409497,0.33389192851356975,40,0.675,0.725,0.65,0.7
equities,1.2,0.2,2.0,views_full_conf,0.1208358090685211,0.1388148669631386,0.2520468478715272,0.4274519380538496,0.2809864122504722,0.6562121951380189,0.7043314230261237,-0.32766221473726487,1.5775354328201663,3.1438323088310356,0.468223850876543,40,0.625,0.675,0.625,0.625
equities,1.2,0.2,2.0,views_stated_conf,0.11878784135520637,0.14035423799334545,0.25221066889171556,0.416367348786932,0.301816491371558,0.6464369894382871,0.7010262148965498,-0.3309343335357049,1.5660434618176207,3.2067704664107843,0.4666845977719441,40,0.675,0.65,0.675,0.625
equities,1.2,0.4,1.0,equal_weight,0.12341059365887486,0.12675011450781187,0.2256558477961915,0.46851391738540443,0.3248717034062219,0.642302409312645,0.784591379980037,-0.2855686051005571,1.5920383947690195,5.999999999999999,0.0,40,0.625,0.7,0.425,0.6
equities,1.2,0.4,1.0,market_hold,0.12306716854170785,0.1049495198569231,0.3366874814448674,0.42907420899583437,0.22398392939148923,0.5363240853411446,0.7176054294318316,-0.4283798073581172,1.5901201847861306,1.0,0.0,40,0.35,0.0,0.375,0.0
equities,1.2,0.4,1.0,risk_only,0.13477479333092202,0.1286509297403245,0.26670308279795807,0.44979510366716813,0.2695294930919465,0.6399254587037934,0.7516994286408649,-0.3696834808299144,1.6575375820884322,4.293553439665313,0.017947018026381822,40,0.0,0.65,0.0,0.625
equities,1.2,0.4,1.0,views_calibrated_conf,0.16141666170482105,0.16535440143735175,0.2553468765283427,0.5923195445157929,0.4012606682746331,0.7059463426316521,1.005028574170749,-0.32592716074216593,1.818430796293911,3.652687660247902,0.3637576848924984,40,0.8,0.8,0.775,0.8
equities,1.2,0.4,1.0,views_full_conf,0.1774450821133251,0.16829452555101318,0.25314459160508607,0.6028328857890977,0.40550617796736227,0.7491245663980257,0.992410595918626,-0.31820246476910863,1.9208132849076116,3.144271071069781,0.4738333225871292,40,0.8,0.8,0.8,0.8
equities,1.2,0.4,1.0,views_stated_conf,0.17129125519787225,0.17142641905982908,0.25230256019003205,0.5978127564794287,0.46386600577103315,0.7793718413778632,1.0068308760147011,-0.320141937022459,1.8811861491381638,3.309152694487553,0.445856012233948,40,0.775,0.825,0.75,0.8
equities,1.2,0.4,2.0,equal_weight,0.12341059365887486,0.12675011450781187,0.2256558477961915,0.46851391738540443,0.3248717034062219,0.642302409312645,0.784591379980037,-0.2855686051005571,1.5920383947690195,5.999999999999999,0.0,40,0.625,0.7,0.425,0.6
equities,1.2,0.4,2.0,market_hold,0.12306716854170785,0.1049495198569231,0.3366874814448674,0.42907420899583437,0.22398392939148923,0.5363240853411446,0.7176054294318316,-0.4283798073581172,1.5901201847861306,1.0,0.0,40,0.35,0.0,0.375,0.0
equities,1.2,0.4,2.0,risk_only,0.13477479333092202,0.1286509297403245,0.26670308279795807,0.44979510366716813,0.2695294930919465,0.6399254587037934,0.7516994286408649,-0.3696834808299144,1.6575375820884322,4.293553439665313,0.017947018026381822,40,0.0,0.65,0.0,0.625
equities,1.2,0.4,2.0,views_calibrated_conf,0.16141666170482105,0.16535440143735175,0.2553468765283427,0.5923195445157929,0.4012606682746331,0.7059463426316521,1.005028574170749,-0.32592716074216593,1.818430796293911,3.652687660247902,0.3637576848924984,40,0.8,0.8,0.775,0.8
equities,1.2,0.4,2.0,views_full_conf,0.1774450821133251,0.16829452555101318,0.25314459160508607,0.6028328857890977,0.40550617796736227,0.7491245663980257,0.992410595918626,-0.31820246476910863,1.9208132849076116,3.144271071069781,0.4738333225871292,40,0.8,0.8,0.8,0.8
equities,1.2,0.4,2.0,views_stated_conf,0.1768750587079866,0.168609449918861,0.25291591312921535,0.6017746975849526,0.41053125504350063,0.7496712868066185,0.9982156612624034,-0.3174749909726199,1.9171093440411742,3.151614410511473,0.4720430620614258,40,0.8,0.8,0.8,0.8
equities,2.5,0.0,1.0,equal_weight,0.12341059365887486,0.12675011450781187,0.2256558477961915,0.46851391738540443,0.3248717034062219,0.642302409312645,0.784591379980037,-0.2855686051005571,1.5920383947690195,5.999999999999999,0.0,40,0.375,0.7,0.65,0.6
equities,2.5,0.0,1.0,market_hold,0.12306716854170785,0.1049495198569231,0.3366874814448674,0.42907420899583437,0.22398392939148923,0.5363240853411446,0.7176054294318316,-0.4283798073581172,1.5901201847861306,1.0,0.0,40,0.35,0.0,0.425,0.0
equities,2.5,0.0,1.0,risk_only,0.11740432428246439,0.12364178733994573,0.19984527993904155,0.47062474946745003,0.3207605017923386,0.6326784981375307,0.7842543017812129,-0.25486062613292704,1.558296578514101,5.30587539394206,0.014243237221098545,40,0.0,0.65,0.0,0.575
equities,2.5,0.0,1.0,views_calibrated_conf,0.11313465510681997,0.12094473334568105,0.21289414783854468,0.45576426552178295,0.30275631692615473,0.5446219411398857,0.7630476283400891,-0.28182473541225916,1.5346411945617526,4.7320838158895775,0.19068902986955838,40,0.325,0.65,0.35,0.6
equities,2.5,0.0,1.0,views_full_conf,0.11838198874896089,0.12162059358465341,0.2450826476480676,0.4235742940695136,0.2079365737013044,0.5629468026533679,0.6932510385030328,-0.3278992356205671,1.5637893841155974,3.269614387383589,0.47372031590785435,40,0.4,0.6,0.425,0.55
equities,2.5,0.0,1.0,views_stated_conf,0.11120203164890019,0.1190563034818715,0.23350312880728735,0.4368500653298489,0.2633541564402207,0.5075811515277282,0.7268087331970727,-0.312317008588614,1.5246239481476027,3.7601313954328304,0.4143523995352747,40,0.4,0.6,0.475,0.55
equities,2.5,0.0,2.0,equal_weight,0.12341059365887486,0.12675011450781187,0.2256558477961915,0.46851391738540443,0.3248717034062219,0.642302409312645,0.784591379980037,-0.2855686051005571,1.5920383947690195,5.999999999999999,0.0,40,0.375,0.7,0.65,0.6
equities,2.5,0.0,2.0,market_hold,0.12306716854170785,0.1049495198569231,0.3366874814448674,0.42907420899583437,0.22398392939148923,0.5363240853411446,0.7176054294318316,-0.4283798073581172,1.5901201847861306,1.0,0.0,40,0.35,0.0,0.425,0.0
equities,2.5,0.0,2.0,risk_only,0.11740432428246439,0.12364178733994573,0.19984527993904155,0.47062474946745003,0.3207605017923386,0.6326784981375307,0.7842543017812129,-0.25486062613292704,1.558296578514101,5.30587539394206,0.014243237221098545,40,0.0,0.65,0.0,0.575
equities,2.5,0.0,2.0,views_calibrated_conf,0.11313465510681997,0.12094473334568105,0.21289414783854468,0.45576426552178295,0.30275631692615473,0.5446219411398857,0.7630476283400891,-0.28182473541225916,1.5346411945617526,4.7320838158895775,0.19068902986955838,40,0.325,0.65,0.35,0.6
equities,2.5,0.0,2.0,views_full_conf,0.11838198874896089,0.12162059358465341,0.2450826476480676,0.4235742940695136,0.2079365737013044,0.5629468026533679,0.6932510385030328,-0.3278992356205671,1.5637893841155974,3.269614387383589,0.47372031590785435,40,0.4,0.6,0.425,0.55
equities,2.5,0.0,2.0,views_stated_conf,0.1265771210856853,0.12194692646082717,0.24082728438709816,0.44934653446603645,0.2700275586263273,0.5229075349491343,0.7342698830279144,-0.32168023033792353,1.6100465871863272,3.4444016353352818,0.45883928027541065,40,0.4,0.625,0.425,0.575
equities,2.5,0.2,1.0,equal_weight,0.12341059365887486,0.12675011450781187,0.2256558477961915,0.46851391738540443,0.3248717034062219,0.642302409312645,0.784591379980037,-0.2855686051005571,1.5920383947690195,5.999999999999999,0.0,40,0.375,0.7,0.65,0.6
equities,2.5,0.2,1.0,market_hold,0.12306716854170785,0.1049495198569231,0.3366874814448674,0.42907420899583437,0.22398392939148923,0.5363240853411446,0.7176054294318316,-0.4283798073581172,1.5901201847861306,1.0,0.0,40,0.35,0.0,0.425,0.0
equities,2.5,0.2,1.0,risk_only,0.11740432428246439,0.12364178733994573,0.19984527993904155,0.47062474946745003,0.3207605017923386,0.6326784981375307,0.7842543017812129,-0.25486062613292704,1.558296578514101,5.30587539394206,0.014243237221098545,40,0.0,0.65,0.0,0.575
equities,2.5,0.2,1.0,views_calibrated_conf,0.1288157677144831,0.13913377917888534,0.218228035429691,0.5076583829539789,0.3899320035061888,0.6069325775354258,0.8786315483279725,-0.2875653926223024,1.6228700804044929,4.221669112982984,0.32236306976766516,40,0.65,0.675,0.725,0.65
equities,2.5,0.2,1.0,views_full_conf,0.13426657237824735,0.14506433565001184,0.2435471858689302,0.4697999963990579,0.3502102272570096,0.6262707524003298,0.782508471490614,-0.3092583069309578,1.6544110463047996,3.2881076130087736,0.4734515413168432,40,0.575,0.7,0.625,0.6
equities,2.5,0.2,1.0,views_stated_conf,0.13940098036700355,0.14458894142818593,0.23671941014451675,0.5095625440722631,0.37147277028031944,0.61579622255025,0.8461032298059801,-0.30060687569402705,1.6845807732821445,3.6705231776514085,0.4280284746431409,40,0.6,0.725,0.7,0.6
equities,2.5,0.2,2.0,equal_weight,0.12341059365887486,0.12675011450781187,0.2256558477961915,0.46851391738540443,0.3248717034062219,0.642302409312645,0.784591379980037,-0.2855686051005571,1.5920383947690195,5.999999999999999,0.0,40,0.375,0.7,0.65,0.6
equities,2.5,0.2,2.0,market_hold,0.12306716854170785,0.1049495198569231,0.3366874814448674,0.42907420899583437,0.22398392939148923,0.5363240853411446,0.7176054294318316,-0.4283798073581172,1.5901201847861306,1.0,0.0,40,0.35,0.0,0.425,0.0
equities,2.5,0.2,2.0,risk_only,0.11740432428246439,0.12364178733994573,0.19984527993904155,0.47062474946745003,0.3207605017923386,0.6326784981375307,0.7842543017812129,-0.25486062613292704,1.558296578514101,5.30587539394206,0.014243237221098545,40,0.0,0.65,0.0,0.575
equities,2.5,0.2,2.0,views_calibrated_conf,0.1288157677144831,0.13913377917888534,0.218228035429691,0.5076583829539789,0.3899320035061888,0.6069325775354258,0.8786315483279725,-0.2875653926223024,1.6228700804044929,4.221669112982984,0.32236306976766516,40,0.65,0.675,0.725,0.65
equities,2.5,0.2,2.0,views_full_conf,0.13426657237824735,0.14506433565001184,0.2435471858689302,0.4697999963990579,0.3502102272570096,0.6262707524003298,0.782508471490614,-0.3092583069309578,1.6544110463047996,3.2881076130087736,0.4734515413168432,40,0.575,0.7,0.625,0.6
equities,2.5,0.2,2.0,views_stated_conf,0.13429435900766407,0.14473153527852423,0.24223997796041608,0.4784087025658458,0.35176774208254125,0.6138219021553143,0.7880564792588969,-0.31044599207509116,1.6545809776700802,3.377105739319773,0.46302189772051083,40,0.6,0.7,0.625,0.6
equities,2.5,0.4,1.0,equal_weight,0.12341059365887486,0.12675011450781187,0.2256558477961915,0.46851391738540443,0.3248717034062219,0.642302409312645,0.784591379980037,-0.2855686051005571,1.5920383947690195,5.999999999999999,0.0,40,0.375,0.7,0.65,0.6
equities,2.5,0.4,1.0,market_hold,0.12306716854170785,0.1049495198569231,0.3366874814448674,0.42907420899583437,0.22398392939148923,0.5363240853411446,0.7176054294318316,-0.4283798073581172,1.5901201847861306,1.0,0.0,40,0.35,0.0,0.425,0.0
equities,2.5,0.4,1.0,risk_only,0.11740432428246439,0.12364178733994573,0.19984527993904155,0.47062474946745003,0.3207605017923386,0.6326784981375307,0.7842543017812129,-0.25486062613292704,1.558296578514101,5.30587539394206,0.014243237221098545,40,0.0,0.65,0.0,0.575
equities,2.5,0.4,1.0,views_calibrated_conf,0.16071683623076938,0.1640969451890831,0.22285209865855365,0.6042830003537052,0.49604196702596637,0.7309374155426953,1.039046552490658,-0.27810012869758316,1.8140464928222189,4.049447140201552,0.35722496687675764,40,0.85,0.85,0.875,0.725
equities,2.5,0.4,1.0,views_full_conf,0.17009117243437044,0.17067736203534256,0.24391013277207182,0.6046476991208071,0.4556200558349294,0.7630831108561918,0.9952544509243821,-0.30117871861353657,1.8735116523704982,3.302524159873261,0.46588455237556786,40,0.725,0.8,0.85,0.75
equities,2.5,0.4,1.0,views_stated_conf,0.1674179224347382,0.17428773965652,0.23930582315956148,0.600578443518309,0.5172070204351213,0.7691825602172156,1.003699155267839,-0.2864790346582369,1.856305436019459,3.570518393145261,0.43720690246406335,40,0.825,0.85,0.85,0.725
equities,2.5,0.4,2.0,equal_weight,0.12341059365887486,0.12675011450781187,0.2256558477961915,0.46851391738540443,0.3248717034062219,0.642302409312645,0.784591379980037,-0.2855686051005571,1.5920383947690195,5.999999999999999,0.0,40,0.375,0.7,0.65,0.6
equities,2.5,0.4,2.0,market_hold,0.12306716854170785,0.1049495198569231,0.3366874814448674,0.42907420899583437,0.22398392939148923,0.5363240853411446,0.7176054294318316,-0.4283798073581172,1.5901201847861306,1.0,0.0,40,0.35,0.0,0.425,0.0
equities,2.5,0.4,2.0,risk_only,0.11740432428246439,0.12364178733994573,0.19984527993904155,0.47062474946745003,0.3207605017923386,0.6326784981375307,0.7842543017812129,-0.25486062613292704,1.558296578514101,5.30587539394206,0.014243237221098545,40,0.0,0.65,0.0,0.575
equities,2.5,0.4,2.0,views_calibrated_conf,0.16071683623076938,0.1640969451890831,0.22285209865855365,0.6042830003537052,0.49604196702596637,0.7309374155426953,1.039046552490658,-0.27810012869758316,1.8140464928222189,4.049447140201552,0.35722496687675764,40,0.85,0.85,0.875,0.725
equities,2.5,0.4,2.0,views_full_conf,0.17009117243437044,0.17067736203534256,0.24391013277207182,0.6046476991208071,0.4556200558349294,0.7630831108561918,0.9952544509243821,-0.30117871861353657,1.8735116523704982,3.302524159873261,0.46588455237556786,40,0.725,0.8,0.85,0.75
equities,2.5,0.4,2.0,views_stated_conf,0.17007851664892049,0.17116033474308107,0.2435780492441054,0.6095175067485772,0.4580431859401941,0.7567277781338262,1.0026646569530118,-0.3006597217629532,1.8733186114511893,3.311476336581108,0.4662103163020673,40,0.75,0.8,0.825,0.775
equities,5.0,0.0,1.0,equal_weight,0.12341059365887486,0.12675011450781187,0.2256558477961915,0.46851391738540443,0.3248717034062219,0.642302409312645,0.784591379980037,-0.2855686051005571,1.5920383947690195,5.999999999999999,0.0,40,0.45,0.7,0.65,0.6
equities,5.0,0.0,1.0,market_hold,0.12306716854170785,0.1049495198569231,0.3366874814448674,0.42907420899583437,0.22398392939148923,0.5363240853411446,0.7176054294318316,-0.4283798073581172,1.5901201847861306,1.0,0.0,40,0.325,0.0,0.475,0.0
equities,5.0,0.0,1.0,risk_only,0.11320349055365342,0.11866046300276842,0.18329014987375028,0.4676624468325375,0.35155461632877105,0.6441931362310864,0.7715421638356486,-0.24409155217623546,1.5350341451316372,3.9649777249101366,0.02184233512964734,40,0.0,0.675,0.0,0.525
equities,5.0,0.0,1.0,views_calibrated_conf,0.11767993901769591,0.12153374389687259,0.1926796316628252,0.5109856631442277,0.3500465805602236,0.6348432959461663,0.8489292678860165,-0.25109497783932505,1.5598380748818657,3.9649242210695714,0.10556966999273126,40,0.475,0.675,0.5,0.55
equities,5.0,0.0,1.0,views_full_conf,0.11882623592454356,0.1209702031135084,0.22945620391096727,0.4203019277998358,0.3169481333972486,0.5264891644146963,0.7047386522114178,-0.3215269218733134,1.5664473541632615,3.456525586448702,0.43679179283819997,40,0.45,0.575,0.575,0.575
equities,5.0,0.0,1.0,views_stated_conf,0.11818751165274854,0.12002569958109541,0.2108336595388401,0.45735829999750977,0.29712564433183086,0.5775538660596252,0.7657364142272978,-0.29713904194599194,1.5627053919502802,3.8247844992062703,0.3335431004657933,40,0.425,0.625,0.475,0.575
equities,5.0,0.0,2.0,equal_weight,0.12341059365887486,0.12675011450781187,0.2256558477961915,0.46851391738540443,0.3248717034062219,0.642302409312645,0.784591379980037,-0.2855686051005571,1.5920383947690195,5.999999999999999,0.0,40,0.45,0.7,0.65,0.6
equities,5.0,0.0,2.0,market_hold,0.12306716854170785,0.1049495198569231,0.3366874814448674,0.42907420899583437,0.22398392939148923,0.5363240853411446,0.7176054294318316,-0.4283798073581172,1.5901201847861306,1.0,0.0,40,0.325,0.0,0.475,0.0
equities,5.0,0.0,2.0,risk_only,0.11320349055365342,0.11866046300276842,0.18329014987375028,0.4676624468325375,0.35155461632877105,0.6441931362310864,0.7715421638356486,-0.24409155217623546,1.5350341451316372,3.9649777249101366,0.02184233512964734,40,0.0,0.675,0.0,0.525
equities,5.0,0.0,2.0,views_calibrated_conf,0.11767993901769591,0.12153374389687259,0.1926796316628252,0.5109856631442277,0.3500465805602236,0.6348432959461663,0.8489292678860165,-0.25109497783932505,1.5598380748818657,3.9649242210695714,0.10556966999273126,40,0.475,0.675,0.5,0.55
equities,5.0,0.0,2.0,views_full_conf,0.11882623592454356,0.1209702031135084,0.22945620391096727,0.4203019277998358,0.3169481333972486,0.5264891644146963,0.7047386522114178,-0.3215269218733134,1.5664473541632615,3.456525586448702,0.43679179283819997,40,0.45,0.575,0.575,0.575
equities,5.0,0.0,2.0,views_stated_conf,0.11449934694969599,0.12033212451116149,0.22001337848650893,0.42638008287223605,0.27492367148334024,0.5495397234627806,0.7125072388206249,-0.3061591966972596,1.5421714851857677,3.627831716395915,0.4016360590957204,40,0.45,0.6,0.55,0.575
equities,5.0,0.2,1.0,equal_weight,0.12341059365887486,0.12675011450781187,0.2256558477961915,0.46851391738540443,0.3248717034062219,0.642302409312645,0.784591379980037,-0.2855686051005571,1.5920383947690195,5.999999999999999,0.0,40,0.45,0.7,0.65,0.6
equities,5.0,0.2,1.0,market_hold,0.12306716854170785,0.1049495198569231,0.3366874814448674,0.42907420899583437,0.22398392939148923,0.5363240853411446,0.7176054294318316,-0.4283798073581172,1.5901201847861306,1.0,0.0,40,0.325,0.0,0.475,0.0
equities,5.0,0.2,1.0,risk_only,0.11320349055365342,0.11866046300276842,0.18329014987375028,0.4676624468325375,0.35155461632877105,0.6441931362310864,0.7715421638356486,-0.24409155217623546,1.5350341451316372,3.9649777249101366,0.02184233512964734,40,0.0,0.675,0.0,0.525
equities,5.0,0.2,1.0,views_calibrated_conf,0.12719195213881507,0.1348553615763209,0.19733170410456508,0.5221636924621824,0.4124905778718601,0.6647272292621014,0.8974871566729274,-0.26415415170558604,1.6135911174623097,3.9265028809724,0.2082619036788746,40,0.6,0.7,0.675,0.65
equities,5.0,0.2,1.0,views_full_conf,0.1343979995438579,0.14653203800051257,0.22916788952069927,0.4903848444556608,0.40139547051683516,0.6570896268607112,0.8410081395348541,-0.30360648019837166,1.6551858694366182,3.4721774794933618,0.4373917038433424,40,0.65,0.7,0.7,0.625
equities,5.0,0.2,1.0,views_stated_conf,0.13680455393016389,0.14601065823647005,0.21292595959878202,0.5275904400758513,0.44781494060575094,0.6749708436754178,0.8943810919427801,-0.2788019578932867,1.6692602995973909,3.7918188786742704,0.3571705810307786,40,0.7,0.725,0.775,0.675
equities,5.0,0.2,2.0,equal_weight,0.12341059365887486,0.12675011450781187,0.2256558477961915,0.46851391738540443,0.3248717034062219,0.642302409312645,0.784591379980037,-0.2855686051005571,1.5920383947690195,5.999999999999999,0.0,40,0.45,0.7,0.65,0.6
equities,5.0,0.2,2.0,market_hold,0.12306716854170785,0.1049495198569231,0.3366874814448674,0.42907420899583437,0.22398392939148923,0.5363240853411446,0.7176054294318316,-0.4283798073581172,1.5901201847861306,1.0,0.0,40,0.325,0.0,0.475,0.0
equities,5.0,0.2,2.0,risk_only,0.11320349055365342,0.11866046300276842,0.18329014987375028,0.4676624468325375,0.35155461632877105,0.6441931362310864,0.7715421638356486,-0.24409155217623546,1.5350341451316372,3.9649777249101366,0.02184233512964734,40,0.0,0.675,0.0,0.525
equities,5.0,0.2,2.0,views_calibrated_conf,0.12719195213881507,0.1348553615763209,0.19733170410456508,0.5221636924621824,0.4124905778718601,0.6647272292621014,0.8974871566729274,-0.26415415170558604,1.6135911174623097,3.9265028809724,0.2082619036788746,40,0.6,0.7,0.675,0.65
equities,5.0,0.2,2.0,views_full_conf,0.1343979995438579,0.14653203800051257,0.22916788952069927,0.4903848444556608,0.40139547051683516,0.6570896268607112,0.8410081395348541,-0.30360648019837166,1.6551858694366182,3.4721774794933618,0.4373917038433424,40,0.65,0.7,0.7,0.625
equities,5.0,0.2,2.0,views_stated_conf,0.13279635703847692,0.1454491181201067,0.22408290343046666,0.4869110739716441,0.40320327562422653,0.6364908387307469,0.8387311775168721,-0.30244826783642553,1.6458585385540987,3.5584044495170875,0.42146966804835717,40,0.65,0.7,0.725,0.625
equities,5.0,0.4,1.0,equal_weight,0.12341059365887486,0.12675011450781187,0.2256558477961915,0.46851391738540443,0.3248717034062219,0.642302409312645,0.784591379980037,-0.2855686051005571,1.5920383947690195,5.999999999999999,0.0,40,0.45,0.7,0.65,0.6
equities,5.0,0.4,1.0,market_hold,0.12306716854170785,0.1049495198569231,0.3366874814448674,0.42907420899583437,0.22398392939148923,0.5363240853411446,0.7176054294318316,-0.4283798073581172,1.5901201847861306,1.0,0.0,40,0.325,0.0,0.475,0.0
equities,5.0,0.4,1.0,risk_only,0.11320349055365342,0.11866046300276842,0.18329014987375028,0.4676624468325375,0.35155461632877105,0.6441931362310864,0.7715421638356486,-0.24409155217623546,1.5350341451316372,3.9649777249101366,0.02184233512964734,40,0.0,0.675,0.0,0.525
equities,5.0,0.4,1.0,views_calibrated_conf,0.15565075343423873,0.15588674614037665,0.2017468677831623,0.6217262697028431,0.49701795296745055,0.7658185440956337,1.0426628055009965,-0.2563811790970223,1.7826264223010155,3.8747256432785955,0.2564376705965139,40,0.85,0.85,0.9,0.7
equities,5.0,0.4,1.0,views_full_conf,0.161012375933535,0.17140936683176608,0.22844780533877823,0.5964570932119498,0.48032399105758417,0.7553635646704344,1.0118067151794563,-0.29401536507116877,1.8159114774979255,3.4879644667918983,0.43167720119101105,40,0.825,0.8,0.875,0.75
equities,5.0,0.4,1.0,views_stated_conf,0.16611046719667732,0.17257331454416885,0.2154769898256666,0.6388206009929533,0.516238362568398,0.8128110050575199,1.0973851282306035,-0.26893935910250855,1.847993771380171,3.7406872002309774,0.3701309206048987,40,0.85,0.825,0.925,0.75
equities,5.0,0.4,2.0,equal_weight,0.12341059365887486,0.12675011450781187,0.2256558477961915,0.46851391738540443,0.3248717034062219,0.642302409312645,0.784591379980037,-0.2855686051005571,1.5920383947690195,5.999999999999999,0.0,40,0.45,0.7,0.65,0.6
equities,5.0,0.4,2.0,market_hold,0.12306716854170785,0.1049495198569231,0.3366874814448674,0.42907420899583437,0.22398392939148923,0.5363240853411446,0.7176054294318316,-0.4283798073581172,1.5901201847861306,1.0,0.0,40,0.325,0.0,0.475,0.0
equities,5.0,0.4,2.0,risk_only,0.11320349055365342,0.11866046300276842,0.18329014987375028,0.4676624468325375,0.35155461632877105,0.6441931362310864,0.7715421638356486,-0.24409155217623546,1.5350341451316372,3.9649777249101366,0.02184233512964734,40,0.0,0.675,0.0,0.525
equities,5.0,0.4,2.0,views_calibrated_conf,0.15565075343423873,0.15588674614037665,0.2017468677831623,0.6217262697028431,0.49701795296745055,0.7658185440956337,1.0426628055009965,-0.2563811790970223,1.7826264223010155,3.8747256432785955,0.2564376705965139,40,0.85,0.85,0.9,0.7
equities,5.0,0.4,2.0,views_full_conf,0.161012375933535,0.17140936683176608,0.22844780533877823,0.5964570932119498,0.48032399105758417,0.7553635646704344,1.0118067151794563,-0.29401536507116877,1.8159114774979255,3.4879644667918983,0.43167720119101105,40,0.825,0.8,0.875,0.75
equities,5.0,0.4,2.0,views_stated_conf,0.16115979608329367,0.17153967419317775,0.22799062537262815,0.5990205062360194,0.47995968904869346,0.7513310298707279,1.0208131986765605,-0.29345000725371506,1.816813987193962,3.4996847220799885,0.43096550143742485,40,0.85,0.8,0.875,0.75
equities,8.0,0.0,1.0,equal_weight,0.12341059365887486,0.12675011450781187,0.2256558477961915,0.46851391738540443,0.3248717034062219,0.642302409312645,0.784591379980037,-0.2855686051005571,1.5920383947690195,5.999999999999999,0.0,40,0.525,0.7,0.7,0.6
equities,8.0,0.0,1.0,market_hold,0.12306716854170785,0.1049495198569231,0.3366874814448674,0.42907420899583437,0.22398392939148923,0.5363240853411446,0.7176054294318316,-0.4283798073581172,1.5901201847861306,1.0,0.0,40,0.35,0.0,0.5,0.0
equities,8.0,0.0,1.0,risk_only,0.10836539941372647,0.11751113808426143,0.1820021843711634,0.44810117306221764,0.32471126842729536,0.6252947769901609,0.7664562592497948,-0.24415749112212637,1.508533813482471,3.6827334378275918,0.020564491637672905,40,0.0,0.65,0.0,0.5
equities,8.0,0.0,1.0,views_calibrated_conf,0.11776830828456186,0.12039895974071102,0.18595855120794744,0.5229527724565108,0.3369751862756348,0.6467828357777164,0.8610536886270843,-0.24961202324061402,1.560381305292501,3.7119897357455214,0.06488291188331576,40,0.475,0.675,0.5,0.525
equities,8.0,0.0,1.0,views_full_conf,0.11370802406896108,0.12046703671706252,0.21765482530380462,0.4424306214585021,0.2814278724935927,0.553740039868351,0.7155400428461081,-0.3041189733876024,1.5378237955159082,3.5468950684406204,0.39691426005953856,40,0.475,0.65,0.6,0.6
equities,8.0,0.0,1.0,views_stated_conf,0.11747222406017443,0.12025867777361447,0.20155534671746872,0.4666121369786323,0.35313883551155917,0.619178085267523,0.7817733040361856,-0.2758789542631202,1.5588387503353682,3.7358474417080165,0.25124075100826426,40,0.45,0.65,0.475,0.525
equities,8.0,0.0,2.0,equal_weight,0.12341059365887486,0.12675011450781187,0.2256558477961915,0.46851391738540443,0.3248717034062219,0.642302409312645,0.784591379980037,-0.2855686051005571,1.5920383947690195,5.999999999999999,0.0,40,0.525,0.7,0.7,0.6
equities,8.0,0.0,2.0,market_hold,0.12306716854170785,0.1049495198569231,0.3366874814448674,0.42907420899583437,0.22398392939148923,0.5363240853411446,0.7176054294318316,-0.4283798073581172,1.5901201847861306,1.0,0.0,40,0.35,0.0,0.5,0.0
equities,8.0,0.0,2.0,risk_only,0.10836539941372647,0.11751113808426143,0.1820021843711634,0.44810117306221764,0.32471126842729536,0.6252947769901609,0.7664562592497948,-0.24415749112212637,1.508533813482471,3.6827334378275918,0.020564491637672905,40,0.0,0.65,0.0,0.5
equities,8.0,0.0,2.0,views_calibrated_conf,0.11776830828456186,0.12039895974071102,0.18595855120794744,0.5229527724565108,0.3369751862756348,0.6467828357777164,0.8610536886270843,-0.24961202324061402,1.560381305292501,3.7119897357455214,0.06488291188331576,40,0.475,0.675,0.5,0.525
equities,8.0,0.0,2.0,views_full_conf,0.11370802406896108,0.12046703671706252,0.21765482530380462,0.4424306214585021,0.2814278724935927,0.553740039868351,0.7155400428461081,-0.3041189733876024,1.5378237955159082,3.5468950684406204,0.39691426005953856,40,0.475,0.65,0.6,0.6
equities,8.0,0.0,2.0,views_stated_conf,0.11325608104761664,0.12026953847828359,0.21083971913561467,0.43325870607217665,0.25864657560328896,0.6000524659331865,0.7353974643026531,-0.2949516542882528,1.5353431815835512,3.6538846250128127,0.3477702916382279,40,0.45,0.675,0.5,0.55
equities,8.0,0.2,1.0,equal_weight,0.12341059365887486,0.12675011450781187,0.2256558477961915,0.46851391738540443,0.3248717034062219,0.642302409312645,0.784591379980037,-0.2855686051005571,1.5920383947690195,5.999999999999999,0.0,40,0.525,0.7,0.7,0.6
equities,8.0,0.2,1.0,market_hold,0.12306716854170785,0.1049495198569231,0.3366874814448674,0.42907420899583437,0.22398392939148923,0.5363240853411446,0.7176054294318316,-0.4283798073581172,1.5901201847861306,1.0,0.0,40,0.35,0.0,0.5,0.0
equities,8.0,0.2,1.0,risk_only,0.10836539941372647,0.11751113808426143,0.1820021843711634,0.44810117306221764,0.32471126842729536,0.6252947769901609,0.7664562592497948,-0.24415749112212637,1.508533813482471,3.6827334378275918,0.020564491637672905,40,0.0,0.65,0.0,0.5
equities,8.0,0.2,1.0,views_calibrated_conf,0.12361790366487257,0.13093785815864414,0.18936882639375086,0.5140965283218282,0.37657339338235124,0.682894969090236,0.8784981965325154,-0.24230404566766495,1.5932137267429436,3.7299344480991286,0.13461863648380043,40,0.65,0.75,0.725,0.65
equities,8.0,0.2,1.0,views_full_conf,0.1402818350020958,0.1448659599180292,0.2168354513768211,0.5282131850818006,0.3791710190749251,0.6683337936072501,0.9144632617832842,-0.299424346572043,1.6897829274497385,3.556038830860723,0.3983269885885564,40,0.65,0.725,0.8,0.65
equities,8.0,0.2,1.0,views_stated_conf,0.1383642538954034,0.14235012418617554,0.20354436056828984,0.5509551928116977,0.435341169947284,0.7121985382490792,0.9282730321034036,-0.2612630941807323,1.6784316219284592,3.7378423091538275,0.28320680688054795,40,0.725,0.75,0.8,0.7
equities,8.0,0.2,2.0,equal_weight,0.12341059365887486,0.12675011450781187,0.2256558477961915,0.46851391738540443,0.3248717034062219,0.642302409312645,0.784591379980037,-0.2855686051005571,1.5920383947690195,5.999999999999999,0.0,40,0.525,0.7,0.7,0.6
equities,8.0,0.2,2.0,market_hold,0.12306716854170785,0.1049495198569231,0.3366874814448674,0.42907420899583437,0.22398392939148923,0.5363240853411446,0.7176054294318316,-0.4283798073581172,1.5901201847861306,1.0,0.0,40,0.35,0.0,0.5,0.0
equities,8.0,0.2,2.0,risk_only,0.10836539941372647,0.11751113808426143,0.1820021843711634,0.44810117306221764,0.32471126842729536,0.6252947769901609,0.7664562592497948,-0.24415749112212637,1.508533813482471,3.6827334378275918,0.020564491637672905,40,0.0,0.65,0.0,0.5
equities,8.0,0.2,2.0,views_calibrated_conf,0.12361790366487257,0.13093785815864414,0.18936882639375086,0.5140965283218282,0.37657339338235124,0.682894969090236,0.8784981965325154,-0.24230404566766495,1.5932137267429436,3.7299344480991286,0.13461863648380043,40,0.65,0.75,0.725,0.65
equities,8.0,0.2,2.0,views_full_conf,0.1402818350020958,0.1448659599180292,0.2168354513768211,0.5282131850818006,0.3791710190749251,0.6683337936072501,0.9144632617832842,-0.299424346572043,1.6897829274497385,3.556038830860723,0.3983269885885564,40,0.65,0.725,0.8,0.65
equities,8.0,0.2,2.0,views_stated_conf,0.13624241689388938,0.14502812748863933,0.2126861948516141,0.5253874372882792,0.40221703638645634,0.6750879472792058,0.9058906921420551,-0.2884700857820768,1.6660272054112435,3.6179619103536007,0.372121816934265,40,0.7,0.75,0.775,0.65
equities,8.0,0.4,1.0,equal_weight,0.12341059365887486,0.12675011450781187,0.2256558477961915,0.46851391738540443,0.3248717034062219,0.642302409312645,0.784591379980037,-0.2855686051005571,1.5920383947690195,5.999999999999999,0.0,40,0.525,0.7,0.7,0.6
equities,8.0,0.4,1.0,market_hold,0.12306716854170785,0.1049495198569231,0.3366874814448674,0.42907420899583437,0.22398392939148923,0.5363240853411446,0.7176054294318316,-0.4283798073581172,1.5901201847861306,1.0,0.0,40,0.35,0.0,0.5,0.0
equities,8.0,0.4,1.0,risk_only,0.10836539941372647,0.11751113808426143,0.1820021843711634,0.44810117306221764,0.32471126842729536,0.6252947769901609,0.7664562592497948,-0.24415749112212637,1.508533813482471,3.6827334378275918,0.020564491637672905,40,0.0,0.65,0.0,0.5
equities,8.0,0.4,1.0,views_calibrated_conf,0.14840626550815128,0.14884314399475196,0.1930623181104143,0.6203657795809845,0.4699999506024942,0.7531526896463758,1.0386946678017583,-0.2458779703663167,1.7384090073145904,3.742958386361516,0.17626441250465472,40,0.875,0.825,0.9,0.725
equities,8.0,0.4,1.0,views_full_conf,0.16808931642196567,0.17194079063505682,0.21581767476360422,0.6682473682960981,0.4682043190602973,0.7750126471158791,1.142239853784257,-0.2745681046272106,1.8605486046485165,3.5664250693056987,0.388881656007399,40,0.875,0.8,0.925,0.75
equities,8.0,0.4,1.0,views_stated_conf,0.16373200881200178,0.16675063762463255,0.20519456576078496,0.6587152102792488,0.5083018252163142,0.8327507308719875,1.13351196372333,-0.2476853140684978,1.8329499165210632,3.7123300226890894,0.30866115621774826,40,0.9,0.825,0.9,0.75
equities,8.0,0.4,2.0,equal_weight,0.12341059365887486,0.12675011450781187,0.2256558477961915,0.46851391738540443,0.3248717034062219,0.642302409312645,0.784591379980037,-0.2855686051005571,1.5920383947690195,5.999999999999999,0.0,40,0.525,0.7,0.7,0.6
equities,8.0,0.4,2.0,market_hold,0.12306716854170785,0.1049495198569231,0.3366874814448674,0.42907420899583437,0.22398392939148923,0.5363240853411446,0.7176054294318316,-0.4283798073581172,1.5901201847861306,1.0,0.0,40,0.35,0.0,0.5,0.0
equities,8.0,0.4,2.0,risk_only,0.10836539941372647,0.11751113808426143,0.1820021843711634,0.44810117306221764,0.32471126842729536,0.6252947769901609,0.7664562592497948,-0.24415749112212637,1.508533813482471,3.6827334378275918,0.020564491637672905,40,0.0,0.65,0.0,0.5
equities,8.0,0.4,2.0,views_calibrated_conf,0.14840626550815128,0.14884314399475196,0.1930623181104143,0.6203657795809845,0.4699999506024942,0.7531526896463758,1.0386946678017583,-0.2458779703663167,1.7384090073145904,3.742958386361516,0.17626441250465472,40,0.875,0.825,0.9,0.725
equities,8.0,0.4,2.0,views_full_conf,0.16808931642196567,0.17194079063505682,0.21581767476360422,0.6682473682960981,0.4682043190602973,0.7750126471158791,1.142239853784257,-0.2745681046272106,1.8605486046485165,3.5664250693056987,0.388881656007399,40,0.875,0.8,0.925,0.75
equities,8.0,0.4,2.0,views_stated_conf,0.16707856772126106,0.1718772385138862,0.21537386492256386,0.6688577169241203,0.476036031362756,0.7795520424560285,1.1397995302261252,-0.2739667803368111,1.854175455278615,3.572745011921357,0.38519861565322727,40,0.875,0.8,0.925,0.75
`,xi=Object.assign({"../../../docs/ADAPTIVE_ELICITATION.md":ju,"../../../docs/BACKTEST_CONVICTION.md":Uu,"../../../docs/BEHAVIOR_GAP.md":Vu,"../../../docs/BROKERAGES.md":Wu,"../../../docs/CALIBRATION.md":$u,"../../../docs/CRYPTO_RESEARCH.md":Ku,"../../../docs/FLEXIBLE_VIEWS.md":Gu,"../../../docs/HEDGE_MODEL.md":Yu,"../../../docs/PREDICTION_MARKETS.md":Qu,"../../../docs/QLORA.md":Xu,"../../../docs/ROADMAP.md":Ju,"../../../docs/SUPABASE.md":Zu,"../../../docs/TAIL_RISK.md":e2,"../../../docs/VISION.md":n2}),s2=Object.assign({"../../../README.md":t2}),_i=Object.assign({"../../../research/conviction/results/diagnostics_crypto.csv":i2,"../../../research/conviction/results/diagnostics_equities.csv":r2,"../../../research/conviction/results/summary_crypto.csv":o2,"../../../research/conviction/results/summary_equities.csv":a2}),l2=e=>{const n=Object.keys(xi).find(t=>t.endsWith(`/${e}`));return n?xi[n]:""},u2=()=>Object.values(s2)[0]||"";function c2(e){const n=tn[e];if(!n)return null;const t=n.file==="README.md"?u2():l2(n.file);return{slug:e,...n,body:t}}function g2(e){const n=Object.keys(_i).find(a=>a.endsWith(`/${e}.csv`));if(!n)return[];const[t,...i]=_i[n].trim().split(`
`),r=t.split(",");return i.map(a=>{const o=a.split(","),s={};return r.forEach((l,u)=>{const c=Number(o[u]);s[l]=o[u]!==""&&Number.isFinite(c)?c:o[u]}),s})}const h2={methodology:{title:"Methodology",lede:"Every model, equation, assumption, parameter and limitation — the same documents the code is built from, unabridged."},setup:{title:"Setup",lede:"Try the demo with no setup, connect a paper account, run Hone yourself, or turn on accounts."}};function d2({kind:e="methodology"}){const n=Gr(),t=h2[e];return L.jsxs(L.Fragment,{children:[L.jsxs("div",{className:"container docs-head",children:[L.jsx("div",{className:"eyebrow mb-2",children:n.brand}),L.jsx("h1",{children:t.title}),L.jsx("p",{className:"lede mt-3",children:t.lede}),e==="setup"&&L.jsx(p2,{product:n})]}),L.jsx(zr,{kind:e,product:n})]})}function zr({kind:e,product:n}){var p;const{doc:t}=Yr(),i=((p=Qr[n.slug])==null?void 0:p[e])||[],r=t||i[0],o=i.includes(r)?c2(r):null,s=Qe.useRef(null),[l,u]=Qe.useState([]),[c,h]=Qe.useState(null);return Qe.useEffect(()=>{const d=s.current;if(!d)return;const f=[...d.querySelectorAll("h2[id], h3[id]")];u(f.map(D=>({id:D.id,text:D.textContent,depth:D.tagName==="H3"?3:2})));const w=new IntersectionObserver(D=>{const y=D.filter(_=>_.isIntersecting).sort((_,x)=>_.boundingClientRect.top-x.boundingClientRect.top);y[0]&&h(y[0].target.id)},{rootMargin:"-80px 0px -70% 0px"});return f.forEach(D=>w.observe(D)),()=>w.disconnect()},[r]),i.length?L.jsxs("div",{className:"container docs",children:[L.jsx("nav",{className:"docs-list","aria-label":`${e} documents`,children:i.map(d=>L.jsx(Xr,{to:Ln(n.slug,e,d),className:()=>d===r?"active":"",children:tn[d].title},d))}),L.jsx("article",{ref:s,style:{minWidth:0},children:o?L.jsxs(L.Fragment,{children:[L.jsxs("div",{className:"doc-meta",children:[L.jsx("span",{children:o.blurb}),L.jsxs("a",{href:`https://github.com/avcool3/hone/blob/main/${o.file==="README.md"?"":"docs/"}${o.file}`,target:"_blank",rel:"noreferrer",children:["Source: ",o.file]})]}),L.jsx(Hu,{productSlug:n.slug,children:o.body})]}):L.jsxs(Jr,{tone:"attention",title:"This document isn’t part of this product’s pages.",children:[tn[r]?`“${tn[r].title}” belongs to a different product.`:"No document has that name."," ","Pick one from the list."]})}),L.jsxs("aside",{className:"docs-toc","aria-label":"On this page",children:[l.length>0&&L.jsx("div",{className:"eyebrow mb-3",children:"On this page"}),l.map(d=>L.jsx("a",{href:`#${d.id}`,className:`depth-${d.depth} ${d.id===c?"is-active":""}`,children:d.text},d.id))]})]}):null}function p2({product:e}){const n=e.slug,t=n==="prediction-markets",i=[{title:"Try the demo",body:"Nothing to install or sign up for. Sample data is labelled everywhere.",to:vn(n),cta:"Open the workspace"},t?{title:"No brokerage needed",body:"Hone reads public Kalshi prices and never holds exchange keys. It only sizes and explains.",to:vn(n,"markets"),cta:"Browse markets"}:{title:"Connect a paper account",body:`Use your own ${e.account} for real prices and holdings. Keys stay in your browser.`,to:vn(n,"settings"),cta:"Data & account"},{title:"Run it yourself",body:"Install the Python package, start the web app, or host it with Docker, Render or Fly.",to:Ln(n,"setup","how-hone-works","install"),cta:"Install steps"},{title:"Accounts (optional)",body:"Turn on sign-in and saved portfolios with Supabase in about ten minutes.",to:Ln(n,"setup","accounts"),cta:"Set up accounts"}];return L.jsx("div",{className:"doc-cards",children:i.map(r=>L.jsxs(Ai,{to:r.to,className:"doc-card",children:[L.jsx("strong",{children:r.title}),L.jsx("span",{children:r.body}),L.jsxs("span",{style:{color:"var(--primary)",fontWeight:600},children:[r.cta," →"]})]},r.title))})}const y2=Object.freeze(Object.defineProperty({__proto__:null,DocReader:zr,default:d2},Symbol.toStringTag,{value:"Module"}));export{zr as D,Hu as M,c2 as a,y2 as b,g2 as g};
