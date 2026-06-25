#!/usr/bin/env python3
"""
validate_site.py — 배포 전 정적 검증 하니스 (PWA 설치 적합성 + 문서 링크 정합성)
외부 라이브러리 없이 Python 표준 라이브러리만 사용합니다.
"""
import os
import sys
import json
import re
import struct

def run_validation(site_dir):
    print(f"=== 정적 사이트 검증 시작: {site_dir} ===")
    all_pass = True
    
    # 1. 필수 파일 존재 점검
    required_files = [
        "index.html",
        "manifest.webmanifest",
        "sw.js",
        "data/latest.json",
        "icons/icon-192.png",
        "icons/icon-512.png"
    ]
    check1_ok = True
    missing_files = []
    for f in required_files:
        p = os.path.join(site_dir, f)
        if not os.path.exists(p):
            check1_ok = False
            missing_files.append(f)
            
    if check1_ok:
        print("[PASS] 1. 필수 파일 존재: 모든 필수 파일이 존재합니다.")
    else:
        print(f"[FAIL] 1. 필수 파일 존재: 누락 파일 -> {', '.join(missing_files)}")
        all_pass = False

    # 2. manifest 유효성 점검
    manifest_path = os.path.join(site_dir, "manifest.webmanifest")
    if os.path.exists(manifest_path):
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
            
            manifest_ok = True
            manifest_reasons = []
            
            # 키 존재 확인
            req_keys = ["name", "short_name", "start_url", "scope", "display", "icons"]
            for k in req_keys:
                if k not in manifest:
                    manifest_ok = False
                    manifest_reasons.append(f"누락된 키: {k}")
            
            # display=="standalone"
            if manifest.get("display") != "standalone":
                manifest_ok = False
                manifest_reasons.append(f"display가 standalone이 아님: {manifest.get('display')}")
                
            # start_url, scope 상대 경로
            start_url = manifest.get("start_url", "")
            scope = manifest.get("scope", "")
            if start_url.startswith("/"):
                manifest_ok = False
                manifest_reasons.append(f"start_url이 절대 경로임: {start_url}")
            if scope.startswith("/"):
                manifest_ok = False
                manifest_reasons.append(f"scope가 절대 경로임: {scope}")
                
            # icons[].src 존재 확인
            icons = manifest.get("icons", [])
            for idx, icon in enumerate(icons):
                src = icon.get("src", "")
                if src.startswith("/"):
                    manifest_ok = False
                    manifest_reasons.append(f"icon[{idx}].src가 절대 경로임: {src}")
                # 상대 경로 확인 (manifest 위치 기준)
                clean_src = src
                if clean_src.startswith("./"):
                    clean_src = clean_src[2:]
                icon_path = os.path.join(site_dir, clean_src)
                if not os.path.exists(icon_path):
                    manifest_ok = False
                    manifest_reasons.append(f"icon[{idx}].src에 해당하는 파일이 없음: {src} -> {icon_path}")
            
            if manifest_ok:
                print("[PASS] 2. manifest 유효성: 스키마 및 상대 경로 규칙을 충족합니다.")
            else:
                print(f"[FAIL] 2. manifest 유효성: {'; '.join(manifest_reasons)}")
                all_pass = False
        except Exception as e:
            print(f"[FAIL] 2. manifest 유효성: JSON 파싱 실패 ({str(e)})")
            all_pass = False
    else:
        print("[FAIL] 2. manifest 유효성: manifest.webmanifest 파일이 없습니다.")
        all_pass = False

    # 3. 아이콘 PNG 검사
    check3_ok = True
    png_reasons = []
    for icon_name, expected_size in [("icons/icon-192.png", 192), ("icons/icon-512.png", 512)]:
        icon_path = os.path.join(site_dir, icon_name)
        if os.path.exists(icon_path):
            with open(icon_path, "rb") as f:
                sig = f.read(8)
                if sig != b"\x89PNG\r\n\x1a\n":
                    check3_ok = False
                    png_reasons.append(f"{icon_name}에 PNG 시그니처가 없음")
                    continue
                # IHDR 확인
                length_bytes = f.read(4)
                chunk_type = f.read(4)
                if chunk_type != b"IHDR":
                    check3_ok = False
                    png_reasons.append(f"{icon_name}의 첫 번째 청크가 IHDR이 아님 ({chunk_type})")
                    continue
                
                ihdr_data = f.read(13)
                if len(ihdr_data) < 8:
                    check3_ok = False
                    png_reasons.append(f"{icon_name}의 IHDR 데이터가 너무 짧음")
                    continue
                
                width, height = struct.unpack(">II", ihdr_data[0:8])
                if width != expected_size or height != expected_size:
                    check3_ok = False
                    png_reasons.append(f"{icon_name} 크기 불일치: 예상 {expected_size}x{expected_size}, 실제 {width}x{height}")
        else:
            check3_ok = False
            png_reasons.append(f"{icon_name} 파일이 없음")
            
    if check3_ok:
        print("[PASS] 3. 아이콘 PNG 검사: 아이콘들의 PNG 포맷 및 해상도가 올바릅니다.")
    else:
        print(f"[FAIL] 3. 아이콘 PNG 검사: {'; '.join(png_reasons)}")
        all_pass = False

    # 4. service worker precache 정합성
    sw_path = os.path.join(site_dir, "sw.js")
    if os.path.exists(sw_path):
        try:
            with open(sw_path, "r", encoding="utf-8") as f:
                sw_content = f.read()
            
            # SHELL 배열 추출
            precache_urls = re.findall(r'["\'](\./[^"\']*)["\']', sw_content)
            
            sw_ok = True
            sw_reasons = []
            
            for url in precache_urls:
                clean_url = url.split("?")[0]
                if clean_url == "./":
                    continue
                
                path_on_disk = os.path.join(site_dir, clean_url.lstrip("./"))
                if not os.path.exists(path_on_disk):
                    sw_ok = False
                    sw_reasons.append(f"precache 파일 존재하지 않음: {url} -> {path_on_disk}")
            
            if sw_ok:
                print(f"[PASS] 4. service worker precache 정합: {len(precache_urls)}개 항목이 검증되었습니다.")
            else:
                print(f"[FAIL] 4. service worker precache 정합: {'; '.join(sw_reasons)}")
                all_pass = False
        except Exception as e:
            print(f"[FAIL] 4. service worker precache 정합: 읽기/파싱 실패 ({str(e)})")
            all_pass = False
    else:
        print("[FAIL] 4. service worker precache 정합: sw.js 파일이 없음")
        all_pass = False

    # 5. index.html PWA 메타 점검
    index_path = os.path.join(site_dir, "index.html")
    if os.path.exists(index_path):
        try:
            with open(index_path, "r", encoding="utf-8") as f:
                index_content = f.read()
            
            meta_ok = True
            meta_reasons = []
            
            # viewport
            if "name=\"viewport\"" not in index_content and "name='viewport'" not in index_content:
                meta_ok = False
                meta_reasons.append("name=\"viewport\" 메타 태그 누락")
            # rel="manifest"
            if "rel=\"manifest\"" not in index_content and "rel='manifest'" not in index_content:
                meta_ok = False
                meta_reasons.append("rel=\"manifest\" 링크 태그 누락")
            # theme-color
            if "name=\"theme-color\"" not in index_content and "name='theme-color'" not in index_content:
                meta_ok = False
                meta_reasons.append("name=\"theme-color\" 메타 태그 누락")
            # serviceWorker.register
            if "serviceWorker.register" not in index_content:
                meta_ok = False
                meta_reasons.append("serviceWorker.register 스크립트 등록 코드 누락")
                
            if meta_ok:
                print("[PASS] 5. index.html PWA 메타: 모든 필수 메타 및 스크립트가 존재합니다.")
            else:
                print(f"[FAIL] 5. index.html PWA 메타: {', '.join(meta_reasons)}")
                all_pass = False
        except Exception as e:
            print(f"[FAIL] 5. index.html PWA 메타: 파일 읽기 실패 ({str(e)})")
            all_pass = False
    else:
        print("[FAIL] 5. index.html PWA 메타: index.html 파일이 없음")
        all_pass = False

    # 6. 절대경로 부재 점검
    abs_ok = True
    abs_reasons = []
    for f_name in ["index.html", "manifest.webmanifest", "sw.js"]:
        f_path = os.path.join(site_dir, f_name)
        if os.path.exists(f_path):
            with open(f_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # href="/... 또는 src="/... 검사 (단 href="//, src="// 프로토콜 상대 경로는 허용)
            href_src_abs = re.findall(r'(?:href|src)\s*=\s*["\']/[^/][^"\']*["\']', content)
            if href_src_abs:
                abs_ok = False
                abs_reasons.append(f"{f_name}에 절대 경로 속성 존재: {href_src_abs}")
                
            # JS/JSON 내부 절대 경로 문자열 리터럴 검사 (단 프로토콜 http:// 또는 https:// 는 제외)
            literal_abs = re.findall(r'["\']/[^/][^"\']*["\']', content)
            filtered_literal = []
            for lit in literal_abs:
                val = lit.strip("\"'")
                if not val.startswith("//") and not val.startswith("http") and not val.startswith("mailto:"):
                    # Skip string literals used as .endsWith() or .indexOf() arguments (path suffix/check, not reference)
                    if re.search(r'(?:endsWith|indexOf)\s*\(\s*' + re.escape(lit) + r'\s*\)', content):
                        continue
                    if val.startswith("/data") or val.startswith("/icons") or val == "/":
                        filtered_literal.append(lit)
            
            if filtered_literal:
                abs_ok = False
                abs_reasons.append(f"{f_name}에 절대 경로 문자열 리터럴 존재: {filtered_literal}")
                
    if abs_ok:
        print("[PASS] 6. 절대경로 부재: index.html/manifest/sw.js에 절대 경로 참조가 없습니다.")
    else:
        print(f"[FAIL] 6. 절대경로 부재: {'; '.join(abs_reasons)}")
        all_pass = False

    # 7. latest.json 스키마 점검
    latest_path = os.path.join(site_dir, "data/latest.json")
    if os.path.exists(latest_path):
        try:
            with open(latest_path, "r", encoding="utf-8") as f:
                latest = json.load(f)
            
            schema_ok = True
            schema_reasons = []
            
            # 필수 키
            req_keys = ["updated_at", "tz", "ref_close", "market", "signal", "prices", "target", "conclusion", "disclaimer"]
            for k in req_keys:
                if k not in latest:
                    schema_ok = False
                    schema_reasons.append(f"latest.json 누락 키: {k}")
                    
            # signal.state 검증
            signal = latest.get("signal", {})
            state = signal.get("state")
            if state not in ["ON", "OFF", "NEUTRAL"]:
                schema_ok = False
                schema_reasons.append(f"유효하지 않은 signal.state: {state}")
                
            if schema_ok:
                print("[PASS] 7. latest.json 스키마: 올바른 스키마와 데이터 포맷을 보유하고 있습니다.")
            else:
                print(f"[FAIL] 7. latest.json 스키마: {'; '.join(schema_reasons)}")
                all_pass = False
        except Exception as e:
            print(f"[FAIL] 7. latest.json 스키마: JSON 파싱 실패 ({str(e)})")
            all_pass = False
    else:
        print("[FAIL] 7. latest.json 스키마: latest.json 파일이 없음")
        all_pass = False

    # 8. 문서 상대 링크 정합성 점검 (README.md, RESEARCH.md)
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    broken_links = {}
    
    for doc_name in ["README.md", "RESEARCH.md"]:
        doc_path = os.path.join(repo_root, doc_name)
        if os.path.exists(doc_path):
            with open(doc_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # 마크다운 상대 링크 검출
            links = re.findall(r'\[[^\]]*\]\((.*?)\)', content)
            broken = []
            for link in links:
                clean_link = link.split()[0].strip("\"'")
                clean_link = clean_link.split("#")[0]
                clean_link = clean_link.split("?")[0]
                
                if not clean_link:
                    continue
                if clean_link.startswith("http://") or clean_link.startswith("https://") or clean_link.startswith("mailto:"):
                    continue
                
                # file:// 프로토콜 처리
                if clean_link.startswith("file:///"):
                    target_path = clean_link[7:]
                else:
                    target_path = os.path.normpath(os.path.join(repo_root, clean_link))
                
                if not os.path.exists(target_path):
                    broken.append(f"{link} -> {target_path}")
                    
            if broken:
                broken_links[doc_name] = broken
                all_pass = False
                
    if not broken_links:
        print("[PASS] 8. 문서 링크 정합성: README.md 및 RESEARCH.md의 모든 상대 링크가 유효합니다.")
    else:
        print("[FAIL] 8. 문서 링크 정합성: 깨진 상대 링크 발견")
        for doc_name, broken in broken_links.items():
            print(f"  - {doc_name} 내 누락된 경로:")
            for b in broken:
                print(f"    * {b}")

    # 9. 리밸런싱 로직 단위테스트 실행
    print("9. 리밸런싱 로직 단위테스트 검사...")
    import subprocess
    try:
        # Get path to test script relative to repo root
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        test_script = os.path.join(repo_root, "web", "test_rebalance.mjs")
        res = subprocess.run(["node", test_script], capture_output=True, text=True, check=False)
        if res.returncode == 0:
            print("[PASS] 9. 리밸런싱 단위테스트: 모든 단위테스트가 통과했습니다.")
        else:
            print(f"[FAIL] 9. 리밸런싱 단위테스트 실패 (exit {res.returncode}):")
            print(res.stdout)
            print(res.stderr)
            all_pass = False
    except Exception as e:
        print(f"[FAIL] 9. 리밸런싱 단위테스트 실행 오류: {str(e)}")
        all_pass = False

    # 10. jTicker select 정적 검사 (Req1)
    tpl_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web", "template_index.html")
    check10_ok = True
    check10_reasons = []
    if os.path.exists(tpl_path):
        with open(tpl_path, "r", encoding="utf-8") as f:
            tpl_content = f.read()
        if 'select id="jTicker"' not in tpl_content:
            check10_ok = False
            check10_reasons.append("jTicker가 <select>가 아님")
        if 'SOXL' not in tpl_content.split('select id="jTicker"')[1].split('</select>')[0] if 'select id="jTicker"' in tpl_content else '':
            check10_ok = False
            check10_reasons.append("select에 SOXL option 누락")
        if 'QLD' not in tpl_content.split('select id="jTicker"')[1].split('</select>')[0] if 'select id="jTicker"' in tpl_content else '':
            check10_ok = False
            check10_reasons.append("select에 QLD option 누락")
    else:
        check10_ok = False
        check10_reasons.append("template_index.html 파일 없음")

    if check10_ok:
        print("[PASS] 10. jTicker <select> 검사: SOXL/QLD option 포함.")
    else:
        print(f"[FAIL] 10. jTicker <select> 검사: {'; '.join(check10_reasons)}")
        all_pass = False

    # 11. 리밸런싱 카드 템플릿 문자열 검사 (Req3)
    check11_ok = True
    check11_reasons = []
    if os.path.exists(tpl_path):
        with open(tpl_path, "r", encoding="utf-8") as f:
            tpl_content = f.read()
        if '현재' not in tpl_content:
            check11_ok = False
            check11_reasons.append("현재배분 표시(currentPct) 문자열 누락")
        if '매수' not in tpl_content or '매도' not in tpl_content:
            check11_ok = False
            check11_reasons.append("매수/매도 액션 문자열 누락")
        if '목표' not in tpl_content:
            check11_ok = False
            check11_reasons.append("목표(targetPct) 문자열 누락")
    else:
        check11_ok = False
        check11_reasons.append("template_index.html 파일 없음")

    if check11_ok:
        print("[PASS] 11. 리밸런싱 카드 문자열 검사: 현재배분·매수/매도·목표 키워드 존재.")
    else:
        print(f"[FAIL] 11. 리밸런싱 카드 문자열 검사: {'; '.join(check11_reasons)}")
        all_pass = False

    print(f"=== 검증 완료: 결과 = {'통과(PASS)' if all_pass else '실패(FAIL)'} ===")
    return 0 if all_pass else 1

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법: python3 web/validate_site.py <site_dir>")
        sys.exit(1)
    
    site_dir = sys.argv[1]
    code = run_validation(site_dir)
    sys.exit(code)
