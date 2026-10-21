# kor-review-taker 자가 복구용 네트워크 분석 헬퍼. `source` 해서 쓴다. 절차는 references/self-heal.md.
#   export BSK_SID=<bsk session id>   # bsk session start --browser <id> --no-focus --json 의 session_id
B="${BSK_BIN:-$HOME/.local/bin/bsk}"

# 캡처를 새로 시작하고 상품 페이지로 이동한 뒤 끝까지 스크롤: kr_open <이름> <URL>
kr_open() {
  $B debug stop --session "$BSK_SID" >/dev/null 2>&1
  $B debug start --session "$BSK_SID" --name "$1" >/dev/null 2>&1
  $B navigate "$2" --session "$BSK_SID" 2>&1 | head -2
  for _ in 1 2 3 4 5 6 7 8; do $B wheel --delta-y 1200 --session "$BSK_SID" >/dev/null 2>&1; sleep 0.7; done
  $B debug wait --session "$BSK_SID" --wait-ms 4000 >/dev/null 2>&1
}

# 메인 프레임 캡처 전체(XHR·Fetch)를 next_since 로 넘기며 URL 정규식으로 거른다: kr_xhr [정규식]
kr_xhr() {
  local re="${1:-review|Review|comment|Comment|rvw|postng|gdas|grade|estim}" t since out
  for t in XHR Fetch; do
    since=""
    for _ in 1 2 3 4 5 6 7 8 9 10; do
      out=$($B debug requests --session "$BSK_SID" --resource-type $t --limit 100 ${since:+--since $since} --fields id,method,url,status 2>&1)
      printf '%s' "$out" | node -e 'const re=new RegExp(process.argv[1]);let s="";process.stdin.on("data",d=>s+=d).on("end",()=>{let j;try{j=JSON.parse(s)}catch{return}for(const r of j.requests||[])if(re.test(r.url)&&!/rake|log\/|beacon|collect|gtm|analytics|track|pixel|criteo|doubleclick|sentry/.test(r.url))console.log(r.id,r.method,r.status,r.url.slice(0,220))})' "$re"
      since=$(printf '%s' "$out" | node -e 'let s="";process.stdin.on("data",d=>s+=d).on("end",()=>{try{const j=JSON.parse(s);process.stdout.write((j.requests||[]).length===100&&j.run?.next_since?String(j.run.next_since):"")}catch{}})')
      [ -z "$since" ] && break
    done
  done
}

# 같은 출처 iframe 까지 포함한 XHR/fetch 리소스(캡처가 못 보는 iframe 요청용): kr_perf [정규식]
kr_perf() {
  $B evaluate --session "$BSK_SID" --json "(()=>{const re=new RegExp('${1:-review|Review|comment|rvw|postng|gdas}');const ws=[window];for(const f of document.querySelectorAll('iframe')){try{if(f.contentWindow.document)ws.push(f.contentWindow)}catch(e){}}const o=new Set();for(const w of ws)for(const e of w.performance.getEntriesByType('resource'))if(/xmlhttprequest|fetch/.test(e.initiatorType)&&re.test(e.name))o.add((w===window?'main ':'iframe ')+e.name.slice(0,240));return [...o]})()" \
    | node -e 'let s="";process.stdin.on("data",d=>s+=d).on("end",()=>console.log((JSON.parse(s).value||[]).join("\n")))'
}

# 요청 하나의 URL·요청 본문·주요 헤더·응답 앞부분: kr_req <request-id> [응답 글자 수]
kr_req() {
  $B debug request "$1" --session "$BSK_SID" --part request 2>&1 | node -e 'let s="";process.stdin.on("data",d=>s+=d).on("end",()=>{const r=JSON.parse(s).request;console.log("URL :",r.method,r.url);console.log("BODY:",(r.request_body?.text||"").slice(0,600))})'
  $B debug request "$1" --session "$BSK_SID" --part headers 2>&1 | grep -iE '"(content-type|accept|x-[a-z-]+)"' | head -10
  $B debug request "$1" --session "$BSK_SID" --part response --budget 16384 2>&1 | node -e 'let s="";process.stdin.on("data",d=>s+=d).on("end",()=>{const b=JSON.parse(s).request.response_body;console.log("RESP:",b.state,(b.text||"").slice(0,+process.argv[1]))})' "${2:-1500}"
}

# 화면에서 리뷰 탭·페이지 번호·더보기 후보 찾기 (클릭은 bsk click @eN 으로 직접): kr_controls
kr_controls() {
  $B observe --session "$BSK_SID" 2>&1 | grep -nE '(리뷰|상품평|후기)[^"]*"|(link|button) "([2-9]|다음|더보기|전체보기)' | head -30
}
