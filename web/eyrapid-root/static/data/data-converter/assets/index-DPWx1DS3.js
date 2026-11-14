var R=Object.defineProperty;var _=e=>{throw TypeError(e)};var q=(e,n,r)=>n in e?R(e,n,{enumerable:!0,configurable:!0,writable:!0,value:r}):e[n]=r;var v=(e,n,r)=>q(e,typeof n!="symbol"?n+"":n,r),B=(e,n,r)=>n.has(e)||_("Cannot "+r);var h=(e,n,r)=>(B(e,n,"read from private field"),r?r.call(e):n.get(e)),D=(e,n,r)=>n.has(e)?_("Cannot add the same private member more than once"):n instanceof WeakSet?n.add(e):n.set(e,r),w=(e,n,r,l)=>(B(e,n,"write to private field"),l?l.call(e,r):n.set(e,r),r);/*!
 * Copyright (c) Squirrel Chat et al., All rights reserved.
 * SPDX-License-Identifier: BSD-3-Clause
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 *
 * 1. Redistributions of source code must retain the above copyright notice, this
 *    list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice,
 *    this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 * 3. Neither the name of the copyright holder nor the names of its contributors
 *    may be used to endorse or promote products derived from this software without
 *    specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
 * ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
 * WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
 * DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
 * FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
 * DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
 * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
 * CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
 * OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */function G(e,n){let r=e.slice(0,n).split(/\r?\n/);return[r.length,r.pop().length+1]}function Y(e,n,r){let l=e.split(/\r?\n/),a="",t=(Math.log10(n+1)|0)+1;for(let i=n-1;i<=n+1;i++){let s=l[i-1];s&&(a+=i.toString().padEnd(t," "),a+=":  ",a+=s,a+=`
`,i===n&&(a+=" ".repeat(t+r+2),a+=`^
`))}return a}class o extends Error{constructor(r,l){const[a,t]=G(l.toml,l.ptr),i=Y(l.toml,a,t);super(`Invalid TOML document: ${r}

${i}`,l);v(this,"line");v(this,"column");v(this,"codeblock");this.line=a,this.column=t,this.codeblock=i}static x(r,l,a){throw new o(r,{toml:l.s,ptr:a??l.p})}}/*!
 * Copyright (c) Squirrel Chat et al., All rights reserved.
 * SPDX-License-Identifier: BSD-3-Clause
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 *
 * 1. Redistributions of source code must retain the above copyright notice, this
 *    list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice,
 *    this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 * 3. Neither the name of the copyright holder nor the names of its contributors
 *    may be used to endorse or promote products derived from this software without
 *    specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
 * ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
 * WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
 * DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
 * FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
 * DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
 * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
 * CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
 * OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */function U(e){let n=e.p,r=e.s.charCodeAt(e.p++),l=r,a=r===39,t=r===e.s.charCodeAt(e.p)&&r===e.s.charCodeAt(e.p+1);t&&((r=e.s.charCodeAt(e.p+=2))===10?e.p++:r===13&&e.s.charCodeAt(e.p+1)===10&&(e.p+=2));let i="",s=e.p,u=0;for(;e.p<e.s.length;e.p++)if(r=e.s.charCodeAt(e.p),t&&(r===10||r===13&&e.s.charCodeAt(e.p+1)===10))u=u&&3;else if(r<32&&r!==9||r===127)o.x("control characters are not allowed in strings",e);else if((!u||u===3)&&r===l&&(!t||e.s.charCodeAt(e.p+1)===l&&e.s.charCodeAt(e.p+2)===l)){if(t&&(e.s.charCodeAt(e.p+3)===l&&e.p++,e.s.charCodeAt(e.p+3)===l&&e.p++),!u){let f=e.s.slice(s,e.p);i=i?i+f:f}return e.p+=t?3:1,i}else if(!u)!a&&r===92&&(i+=e.s.slice(s,s=e.p),u=1);else if(u===1)if(r===120||r===117||r===85){let f=e.p++-1,p=0,d=r===120?2:r===117?4:8;for(let g=0;g<d;g++,e.p++){let m=e.s.charCodeAt(e.p),L=m>=48&&m<=57?m-48:m>=65&&m<=70?m-65+10:m>=97&&m<=102?m-97+10:-1;L<0&&o.x("invalid non-hex character in unicode escape",e),p=p<<4|L}(p<0||p>1114111||p>=55296&&p<=57343)&&o.x("invalid unicode escape",e,f),i+=String.fromCodePoint(p),s=e.p--,u=0}else t&&(r===32||r===9)?u=2:(r===98?i+="\b":r===116?i+="	":r===110?i+=`
`:r===102?i+="\f":r===114?i+="\r":r===101?i+="\x1B":r===34?i+='"':r===92?i+="\\":o.x("unrecognised escape sequence",e),s=e.p+1,u=0);else r!==32&&r!==9&&(u===2&&o.x("invalid escape: only line-ending whitespace may be escaped",e,s),u=!a&&r===92?1:0,s=e.p);o.x("unfinished string",e,n)}/*!
 * Copyright (c) Squirrel Chat et al., All rights reserved.
 * SPDX-License-Identifier: BSD-3-Clause
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 *
 * 1. Redistributions of source code must retain the above copyright notice, this
 *    list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice,
 *    this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 * 3. Neither the name of the copyright holder nor the names of its contributors
 *    may be used to endorse or promote products derived from this software without
 *    specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
 * ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
 * WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
 * DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
 * FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
 * DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
 * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
 * CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
 * OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */let H=/^(\d{4}-\d{2}-\d{2})?[Tt ]?(?:(\d{2}):\d{2}(?::\d{2}(?:\.\d+)?)?)?(Z|z|[-+]\d{2}:\d{2})?$/i;var b,y,A;const c=class c extends Date{constructor(r,l,a){let t=!0,i=!0,s="Z",u;if(typeof r=="string")if(l)e:{if(l<3){if(+r.slice(11,13)>23){r="";break e}l===2?(s=null,r+="Z"):(u=r.charCodeAt(r.length-1))!==90&&u!==122&&(s=r.slice(r.length-6)),a&&(r=r.slice(0,10)+"T"+r.slice(11))}else l===4&&(r=+r.slice(0,2)>23?"":`0000-01-01T${r}Z`);t=l!==4,i=l!==3}else{let f=r.match(H);f?(f[1]||(t=!1,r=`0000-01-01T${r}`),i=!!f[2],i&&r[10]===" "&&(r=r.replace(" ","T")),f[2]&&+f[2]>23?r="":(s=f[3]||null,!s&&i&&(r+="Z"))):r=""}super(r);D(this,b,!1);D(this,y,!1);D(this,A,null);isNaN(this.getTime())||(w(this,b,t),w(this,y,i),w(this,A,s))}isDateTime(){return h(this,b)&&h(this,y)}isLocal(){return!h(this,b)||!h(this,y)||!h(this,A)}isDate(){return h(this,b)&&!h(this,y)}isTime(){return h(this,y)&&!h(this,b)}isValid(){return h(this,b)||h(this,y)}toISOString(){let r=super.toISOString();if(this.isDate())return r.slice(0,10);if(this.isTime())return r.slice(11,23);if(h(this,A)===null)return r.slice(0,-1);if(h(this,A)==="Z"||h(this,A)==="z")return r;let l=+h(this,A).slice(1,3)*60+ +h(this,A).slice(4,6);return l=h(this,A)[0]==="-"?l:-l,new Date(this.getTime()-l*6e4).toISOString().slice(0,-1)+h(this,A)}static wrapAsOffsetDateTime(r,l="Z"){let a=new c(r);return w(a,A,l),a}static wrapAsLocalDateTime(r){let l=new c(r);return w(l,A,null),l}static wrapAsLocalDate(r){let l=new c(r);return w(l,y,!1),w(l,A,null),l}static wrapAsLocalTime(r){let l=new c(r);return w(l,b,!1),w(l,A,null),l}};b=new WeakMap,y=new WeakMap,A=new WeakMap;let I=c;/*!
 * Copyright (c) Squirrel Chat et al., All rights reserved.
 * SPDX-License-Identifier: BSD-3-Clause
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 *
 * 1. Redistributions of source code must retain the above copyright notice, this
 *    list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice,
 *    this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 * 3. Neither the name of the copyright holder nor the names of its contributors
 *    may be used to endorse or promote products derived from this software without
 *    specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
 * ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
 * WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
 * DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
 * FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
 * DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
 * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
 * CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
 * OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */function C(e,n=10){return n===16?e>47&&e<58||e>64&&e<71||e>96&&e<103:e>47&&e<48+n}function $(e,n){return e===32||e===9||e===10||e===13||n&&(e===n||e===44)||e===35}function P(e,n){let r=e.p,l=e.s.charCodeAt(e.p);if(l===91||l===123){e.d--||o.x("document contains excessively nested structures. aborting.",e);let a=l===91?ee(e):x(e);return e.d++,a}return l===34||l===39?U(e):l===116?((e.s.charCodeAt(++e.p)!==114||e.s.charCodeAt(++e.p)!==117||e.s.charCodeAt(++e.p)!==101)&&o.x("invalid value",e,r),e.p++,!0):l===102?((e.s.charCodeAt(++e.p)!==97||e.s.charCodeAt(++e.p)!==108||e.s.charCodeAt(++e.p)!==115||e.s.charCodeAt(++e.p)!==101)&&o.x("invalid value",e,r),e.p++,!1):l===43||l===45?S(e,e.p,e.s.charCodeAt(++e.p),44-l,n):e.s.charCodeAt(e.p+4)===45&&e.s.charCodeAt(e.p+7)===45?J(e,l,n):e.s.charCodeAt(e.p+2)===58?Q(e,l,n):S(e,e.p,l,0,n)}function S(e,n,r,l,a){let t=r,i=0,s=!1;if(t===105)return(e.s.charCodeAt(++e.p)!==110||e.s.charCodeAt(++e.p)!==102)&&o.x("invalid value",e,n),e.p++,(l||1)/0;if(t===110)return(e.s.charCodeAt(++e.p)!==97||e.s.charCodeAt(++e.p)!==110)&&o.x("invalid value",e,n),e.p++,NaN;if(t===48){if(++e.p>=e.s.length||$(t=e.s.charCodeAt(e.p),a))return e.bi===!0?0n:0;if(!l){if(t===120)return E(e,n,16,a);if(t===98)return E(e,n,2,a);if(t===111)return E(e,n,8,a)}t===46?i=2:t===101||t===69?i=4:o.x("illegal leading zero",e,n)}else C(t)||o.x("invalid value",e,n);for(;++e.p<e.s.length&&(t=e.s.charCodeAt(e.p),!$(t,a));)i||(i=1),t===95?(i&1||o.x("illegal underscore",e),i+=11,s=!0):i===1&&t===46?i=2:(i===1||i===3)&&(t===101||t===69)?i=4:i===4&&(t===43||t===45)?i=6:C(t)?i>9?i-=11:i&1||i++:o.x("illegal character in numeric literal",e);if(!i){let f=(r-48)*(l||1);return e.bi===!0?BigInt(f):f}i&1||o.x("unfinished numeric value",e,n);let u=e.s.slice(n,e.p);return s&&(u=u.replaceAll("_","")),i>1?parseFloat(u):W(e,u,10,n)}function E(e,n,r,l){let a,t=1;for(;++e.p<e.s.length&&(a=e.s.charCodeAt(e.p),!$(a,l));)a===95?(t&1&&o.x("illegal underscore",e),t=3):C(a,r)?t&1&&t--:o.x("illegal character in numeric literal",e);t&1&&o.x("unfinished numeric value",e);let i=e.s.slice(n+2,e.p);return t&&(i=i.replaceAll("_","")),W(e,i,r,n)}function W(e,n,r,l){if(e.bi!==!0)e:{let a=parseInt(n,r);if(!Number.isSafeInteger(a)){if(e.bi)break e;o.x("integer value cannot be represented losslessly",e,l)}return a}return BigInt(r===10?n:(r===2?"0b":r===8?"0o":"0x")+n)}function J(e,n,r){let l=e.p++,a;if(!C(n)||!C(e.s.charCodeAt(e.p++))||!C(e.s.charCodeAt(e.p++))||!C(e.s.charCodeAt(e.p++)))return S(e,e.p=l,n,0,r);if(e.p+=5,C(e.s.charCodeAt(e.p++))||o.x("invalid date-time: date part is malformed",e,l),e.p>=e.s.length||((n=e.s.charCodeAt(e.p))!==32||(a=!0,!C(e.s.charCodeAt(e.p+1))))&&n!==84&&n!==116){let i=e.s.slice(l,e.p);return k(e,i,3,!1,l)}if(e.s.charCodeAt(e.p+=3)!==58&&o.x("invalid date-time: time part is malformed",e,l),e.s.charCodeAt(e.p+=3)===58&&(e.p+=3),e.s.charCodeAt(e.p)===46)for(;C(e.s.charCodeAt(++e.p)););if(n=e.s.charCodeAt(e.p)){if(n===90||n===122){let i=e.s.slice(l,++e.p);return k(e,i,1,a,l,"[+00:00]")}if(n===43||n===45){let i=e.s.slice(l,e.p+=6);return k(e,i,1,a,l,!e.ld&&"["+e.s.slice(e.p-6,e.p)+"]")}}let t=e.s.slice(l,e.p);return k(e,t,2,a,l)}function Q(e,n,r){let l=e.p;if(!C(n)||!C(e.s.charCodeAt(++e.p)))return S(e,--e.p,n,0,r);if(e.s.charCodeAt(e.p+=4)===58&&(e.p+=3),e.s.charCodeAt(e.p)===46)for(;C(e.s.charCodeAt(++e.p)););let a=e.s.slice(l,e.p);return k(e,a,4,!1,l)}function k(e,n,r,l,a,t){if(e.ld){let i=new I(n,r,l);return i.isValid()||o.x("invalid date",e,a),i}try{switch(t&&(n+=t),r){case 1:return Temporal.ZonedDateTime.from(n);case 2:return Temporal.PlainDateTime.from(n);case 3:return Temporal.PlainDate.from(n);case 4:return Temporal.PlainTime.from(n)}}catch(i){o.x(i instanceof Error?i.message:""+i,e,a)}}/*!
 * Copyright (c) Squirrel Chat et al., All rights reserved.
 * SPDX-License-Identifier: BSD-3-Clause
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 *
 * 1. Redistributions of source code must retain the above copyright notice, this
 *    list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice,
 *    this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 * 3. Neither the name of the copyright holder nor the names of its contributors
 *    may be used to endorse or promote products derived from this software without
 *    specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
 * ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
 * WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
 * DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
 * FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
 * DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
 * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
 * CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
 * OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */function X(e){for(;e.p<e.s.length;e.p++){let n=e.s.charCodeAt(e.p);if(n===10)break;if(n===13&&e.s.charCodeAt(e.p+1)===10){e.p++;break}(n<32&&n!==9||n===127)&&o.x("control characters are not allowed in comments",e)}}function T(e,n,r){let l;for(;e.p<e.s.length;){for(;e.p<e.s.length&&((l=e.s.charCodeAt(e.p))===32||l===9||!n&&(l===10||l===13&&e.s.charCodeAt(e.p+1)===10));)e.p++;if(r||l!==35)break;X(e)}}/*!
 * Copyright (c) Squirrel Chat et al., All rights reserved.
 * SPDX-License-Identifier: BSD-3-Clause
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 *
 * 1. Redistributions of source code must retain the above copyright notice, this
 *    list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice,
 *    this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 * 3. Neither the name of the copyright holder nor the names of its contributors
 *    may be used to endorse or promote products derived from this software without
 *    specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
 * ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
 * WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
 * DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
 * FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
 * DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
 * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
 * CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
 * OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */function N(e,n=61){let r,l=0,a=[],t,i=e.s.charCodeAt(r=e.p);do{if(i===n)return l||o.x("unexpected end of key",e),l===1&&a.push(e.s.slice(t,e.p)),e.p++,a;i===46?(l||o.x("illegal empty bare key",e),l===1&&a.push(e.s.slice(t,e.p)),l=0):!l&&(i===34||i===39)?(i===e.s.charCodeAt(e.p+1)&&i===e.s.charCodeAt(e.p+2)&&o.x("illegal quoted key: multiline strings are not allowed",e),a.push(U(e)),l=2,e.p--):i===32||i===9?l===1&&(a.push(e.s.slice(t,e.p)),l=2):l===2||i<48&&i!==45||i>57&&i<65||i>90&&i<97&&i!==95||i>122?o.x("illegal character in key",e):l||(l=1,t=e.p)}while(i=e.s.charCodeAt(++e.p));o.x("incomplete key-value: cannot find end of key",e,r)}function x(e){let n=e.p++,r=Object.create(null),l=new Set,a;for(;e.p<e.s.length;){if(T(e),(a=e.s.charCodeAt(e.p))===125)return e.p++,r;let t,i=r,s=!1,u=e.p,f=N(e);for(let d=0;d<f.length;d++){d&&(i=s?i[t]:i[t]=Object.create(null)),t=f[d],(s=Object.hasOwn(i,t))&&(typeof i[t]!="object"||l.has(i[t]))&&o.x("trying to redefine an already defined value",e,u);let g=t==="__proto__";if(e.uk&&(g||t==="constructor")){i=e.uk!==1&&o.x("document contains an unsafe property",e,u);break}!s&&g&&Object.defineProperty(i,t,{enumerable:!0,configurable:!0,writable:!0})}s&&o.x("trying to redefine an already defined value",e,u),T(e,!0,!0);let p=P(e,125);if(i&&typeof(i[t]=p)=="object"&&l.add(p),T(e),(a=e.s.charCodeAt(e.p++))===125)return r;a!==44&&o.x("expected comma or end of structure",e,e.p-1)}o.x("unfinished table",e,n)}function ee(e){let n=e.p++,r=[],l;for(;e.p<e.s.length;){if(T(e),(l=e.s.charCodeAt(e.p))===93)return e.p++,r;if(r.push(P(e,93)),T(e),(l=e.s.charCodeAt(e.p++))===93)return r;l!==44&&o.x("expected comma or end of structure",e,e.p-1)}o.x("unfinished array",e,n)}/*!
 * Copyright (c) Squirrel Chat et al., All rights reserved.
 * SPDX-License-Identifier: BSD-3-Clause
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 *
 * 1. Redistributions of source code must retain the above copyright notice, this
 *    list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice,
 *    this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 * 3. Neither the name of the copyright holder nor the names of its contributors
 *    may be used to endorse or promote products derived from this software without
 *    specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
 * ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
 * WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
 * DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
 * FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
 * DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
 * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
 * CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
 * OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */function M(e,n,r,l,a){var p,d;let t=r,i=l,s,u=!1,f;for(let g=0;g<n.length;g++){if(g){if(t=u?t[s]:t[s]=Object.create(null),i=(f=i[s]).c,a===0&&(f.t===1||f.t===2))return null;if(f.t===2){let m=t.length-1;t=t[m],i=i[m].c}}if(s=n[g],(u=Object.hasOwn(t,s))&&((p=i[s])==null?void 0:p.t)===0&&((d=i[s])!=null&&d.d))return null;if(!u){let m=s==="__proto__";if(e.uk&&(m||s==="constructor"))return!1;m&&(Object.defineProperty(t,s,{enumerable:!0,configurable:!0,writable:!0}),Object.defineProperty(i,s,{enumerable:!0,configurable:!0,writable:!0})),i[s]={t:g<n.length-1&&a===2?3:a,d:!1,i:0,c:Object.create(null)}}}if(f=i[s],f.t!==a&&!(a===1&&f.t===3)||(a===2&&(f.d||(f.d=!0,t[s]=[]),t[s].push(t=Object.create(null)),f.c[f.i++]=f={t:1,d:!1,i:0,c:Object.create(null)}),f.d))return null;if(f.d=!0,a===1)t=u?t[s]:t[s]=Object.create(null);else if(a===0&&u)return null;return[s,t,f.c]}function j(e,n,r){(n===null||e.uk===2)&&o.x(n===null?"trying to redefine an already defined table or value":"document contains an unsafe property",e,r)}function re(e,n={}){let r={s:e,p:0,d:n.maxDepth??1e3,bi:n.integersAsBigInt??!1,ld:n.useLegacyDate??!0,uk:n.unsafeKeyBehaviour==="throw"?2:n.unsafeKeyBehaviour==="drop"?1:0},l=Object.create(null),a=Object.create(null),t,i=!1,s=l,u=a;for(e.charCodeAt(0)===65279&&r.p++,T(r);r.p<e.length;){if(e.charCodeAt(r.p)===91){let f=e.charCodeAt(++r.p)===91;t=r.p+=+f,i=!1;let p=N(r,93);f&&(e.charCodeAt(r.p)!==93&&o.x("expected end of table array declaration",r),r.p++);let d=M(r,p,l,a,f?2:1);d?(u=d[2],s=d[1]):(j(r,d,t),i=!0)}else{t=r.p;let f=N(r),p=M(r,f,s,u,0);!p&&!i&&j(r,p,t),T(r,!0,!0);let d=P(r,void 0);p&&!i&&(p[1][p[0]]=d)}T(r,!0),r.p<e.length&&(t=e.charCodeAt(r.p))!==10&&(t!==13||e.charCodeAt(r.p+1)!==10)&&o.x("each key-value declaration must be followed by an end-of-line",r),T(r)}return l}/*!
 * Copyright (c) Squirrel Chat et al., All rights reserved.
 * SPDX-License-Identifier: BSD-3-Clause
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 *
 * 1. Redistributions of source code must retain the above copyright notice, this
 *    list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice,
 *    this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 * 3. Neither the name of the copyright holder nor the names of its contributors
 *    may be used to endorse or promote products derived from this software without
 *    specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
 * ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
 * WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
 * DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
 * FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
 * DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
 * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
 * CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
 * OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */let ie=/^[a-z0-9-_]+$/i,V=!!"".isWellFormed;function O(e){let n=typeof e;if(n==="object"){if(Array.isArray(e))return"array";if(typeof e.getUTCDate=="function"&&e instanceof Date)return"date";if(globalThis.Temporal){if(e.until){if(e instanceof Temporal.ZonedDateTime)return"temporal/tz+uc";if(e instanceof Temporal.PlainDateTime||e instanceof Temporal.PlainDate)return"temporal/uc";if(e instanceof Temporal.PlainTime||e instanceof Temporal.Instant)return"temporal";if(e instanceof Temporal.PlainYearMonth)return"temporal/x"}else if(e.toPlainDate&&e instanceof Temporal.PlainMonthDay||e.negated&&e instanceof Temporal.Duration)return"temporal/x"}}return n}function ne(e){for(let n=0;n<e.length;n++)if(O(e[n])!=="object")return!1;return e.length!=0}function F(e){return JSON.stringify(e).replaceAll("","\\u007f")}function le(e){return F(V?e.toWellFormed():e)}function K(e){if(ie.test(e))return e;if(V&&!e.isWellFormed())throw new RangeError("key contains illegal lone surrogates");return F(e)}function Z(e,n,r,l,a){if(r===0)throw new Error("Could not stringify the object: maximum object depth exceeded");switch(n){case"number":if(isNaN(e))return"nan";if(e===1/0)return"inf";if(e===-1/0)return"-inf";if(Number.isInteger(e)&&(l||!Number.isSafeInteger(e)))return e.toFixed(1);case"bigint":case"boolean":case"temporal":return e.toString();case"string":return le(e);case"date":if(isNaN(e.getTime()))throw new TypeError("cannot serialize invalid date");return e.toISOString();case"object":return te(e,r,l,a);case"array":return ae(e,r,l,a);case"temporal/tz+uc":if(a){let t=e.timeZoneId,i=t.charCodeAt(0);if(i!==43&&i!==45&&(i!==85&&i!==71&&i!==90&&i!==69||t!=="UTC"&&t!=="UCT"&&t!=="Universal"&&t!=="Zulu"&&!t.startsWith("GMT")&&t!=="Greenwich"&&!t.startsWith("Etc/")))throw new TypeError("Temporal objects with an IANA timezone are not allowed in Temporal strict mode")}case"temporal/uc":if(a&&e.calendarId!=="iso8601")throw new TypeError("Temporal objects with a non-default calendar are not allowed in Temporal strict mode");return e.toString({calendarName:"never",timeZoneName:"never"});case"temporal/x":throw new TypeError("Unsupported "+e[Symbol.toStringTag])}}function te(e,n,r,l){let a=Object.keys(e);if(a.length===0)return"{}";let t="{ ";for(let i=0;i<a.length;i++){let s=a[i];i&&(t+=", "),t+=K(s)+" = "+Z(e[s],O(e[s]),n-1,r,l)}return t+" }"}function ae(e,n,r,l){if(e.length===0)return"[]";let a="[ ";for(let t=0;t<e.length;t++){if(t&&(a+=", "),e[t]===null||e[t]===void 0)throw new TypeError("arrays cannot contain null or undefined values");a+=Z(e[t],O(e[t]),n-1,r,l)}return a+" ]"}function se(e,n,r,l,a){if(r===0)throw new Error("Could not stringify the object: maximum object depth exceeded");let t="";for(let i=0;i<e.length;i++)t+=`${t&&`
`}[[${n}]]
`,t+=z(0,e[i],n,r,l,a);return t}function z(e,n,r,l,a,t){if(l===0)throw new Error("Could not stringify the object: maximum object depth exceeded");let i="",s="",u=Object.keys(n);for(let f=0;f<u.length;f++){let p=u[f];if(n[p]!==null&&n[p]!==void 0){let d=O(n[p]);if(d==="symbol"||d==="function")throw new TypeError(`cannot serialize values of type '${d}'`);let g=K(p);if(d==="array"&&ne(n[p]))s+=(s&&`
`)+se(n[p],r?`${r}.${g}`:g,l-1,a,t);else if(d==="object"){let m=r?`${r}.${g}`:g;s+=(s&&`
`)+z(m,n[p],m,l-1,a,t)}else i+=g,i+=" = ",i+=Z(n[p],d,l,a,t),i+=`
`}}return e&&(i||!s)&&(i=i?`[${e}]
${i}`:`[${e}]`),i&&s?`${i}
${s}`:i||s}function fe(e,{maxDepth:n=1e3,numbersAsFloat:r=!1,strictTemporal:l=!1}={}){if(O(e)!=="object")throw new TypeError("stringify can only be called with an object");let a=z(0,e,"",n,r,l);return a[a.length-1]!==`
`?a+`
`:a}/*!
 * Copyright (c) Squirrel Chat et al., All rights reserved.
 * SPDX-License-Identifier: BSD-3-Clause
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 *
 * 1. Redistributions of source code must retain the above copyright notice, this
 *    list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice,
 *    this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 * 3. Neither the name of the copyright holder nor the names of its contributors
 *    may be used to endorse or promote products derived from this software without
 *    specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
 * ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
 * WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
 * DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
 * FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
 * DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
 * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
 * CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
 * OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */const ue={parse:re,stringify:fe,TomlDate:I,TomlError:o};export{I as TomlDate,o as TomlError,ue as default,re as parse,fe as stringify};
