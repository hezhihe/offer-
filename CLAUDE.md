# Offer Compass锛坥ffer缃楃洏锛?
2026 骞村ぇ瀛︾敓灏变笟鎸囧骞冲彴 MVP 鈥?甯姪澶у鐢熺鐞嗘眰鑱岀敵璇枫€佺畝鍘嗗垎鏋愩€侀潰璇曞噯澶囧拰鑱屼笟瑙勫垝鐨勫叏鏍?Web 搴旂敤銆?
## 鎶€鏈爤

- **鍓嶇锛?* Vue 3锛圴ite锛夈€丳inia锛堢姸鎬佺鐞嗭級銆乂ue Router銆佸師鐢?CSS
- **鍚庣锛?* Python FastAPI銆丣WT 璁よ瘉锛坧ython-jose锛夈€乥crypt锛坧asslib锛夈€乽vicorn
- **鏁版嵁搴擄細** Supabase锛圥ostgreSQL锛夛紝閫氳繃 supabase-py 杩炴帴
- **AI 闆嗘垚锛?* DeepSeek V4 Pro 涓轰富妯″瀷锛岀鍩烘祦鍔?V3 涓哄鐢ㄦā鍨嬶紙鍙屾ā鍨嬪鐏撅級
- **鏂囦欢瑙ｆ瀽锛?* pypdf + python-docx锛堢畝鍘嗕笂浼犳敮鎸?PDF/Word锛?
## 椤圭洰缁撴瀯

```
/
鈹溾攢鈹€ backend/
鈹?  鈹溾攢鈹€ main.py             # FastAPI 搴旂敤 鈥?鎵€鏈夎矾鐢便€佽璇併€佹ā鍨嬨€丄I鍒嗘瀽
鈹?  鈹溾攢鈹€ app/services/       # 涓氬姟鏈嶅姟灞傦紙Supabase銆佺敤鎴枫€佸矖浣嶏級
鈹?  鈹溾攢鈹€ database/           # SQL 寤鸿〃涓庣瀛愭暟鎹?鈹?  鈹溾攢鈹€ requirements.txt    # Python 渚濊禆
鈹?  鈹斺攢鈹€ .env                # API 瀵嗛挜涓庢晱鎰熼厤缃?鈹溾攢鈹€ frontend/
鈹?  鈹溾攢鈹€ src/
鈹?  鈹?  鈹溾攢鈹€ api/            # HTTP 瀹㈡埛绔ā鍧楋紙auth銆乯obs銆乺esume銆乮nterview锛?鈹?  鈹?  鈹溾攢鈹€ components/     # 鍙鐢?Vue 缁勪欢锛圔ottomNav銆丮odalDialog銆乀oast锛?鈹?  鈹?  鈹溾攢鈹€ composables/    # 鍏变韩缁勫悎寮忓嚱鏁帮紙useToast锛?鈹?  鈹?  鈹溾攢鈹€ router/         # Vue Router 閰嶇疆
鈹?  鈹?  鈹溾攢鈹€ stores/         # Pinia 鐘舵€佷粨搴擄紙auth銆乮nterview銆乯obs銆乺esume锛?鈹?  鈹?  鈹溾攢鈹€ views/          # 椤甸潰绾х粍浠讹紙Auth銆丠ome銆丆alendar銆両nterview銆丳rofile銆丷esume锛?鈹?  鈹?  鈹溾攢鈹€ App.vue         # 鏍圭粍浠?鈹?  鈹?  鈹斺攢鈹€ main.js         # 搴旂敤鍏ュ彛
鈹?  鈹溾攢鈹€ index.html
鈹?  鈹溾攢鈹€ vite.config.js
鈹?  鈹斺攢鈹€ package.json
鈹溾攢鈹€ docs/                   # 璇︾粏璁捐鏂囨。
鈹溾攢鈹€ seed_test_data.sql     # 娴嬭瘯鏁版嵁 SQL
鈹溾攢鈹€ README.md
鈹溾攢鈹€ CLAUDE.md               # 鏈枃浠讹紙AI 涓婁笅鏂囷級
鈹斺攢鈹€ AGENTS.md               # 鍚屼笂锛堝吋瀹?AGENTS 鍗忚锛?```

## 鍏抽敭绾﹀畾

- **鍓嶇锛?* 鍗曟枃浠?Vue 缁勪欢锛坄<script setup>`锛夛紝姣忎釜棰嗗煙瀵瑰簲涓€涓?Pinia 浠撳簱锛孉PI 璋冪敤闆嗕腑鍦?`src/api/`
- **鍚庣锛?* FastAPI + Pydantic 妯″瀷澶勭悊璇锋眰/鍝嶅簲锛孞WT Token 璁よ瘉锛屾墍鏈夎矾鐢卞湪 `main.py`
- **鐘舵€佺鐞嗭細** Pinia 浠撳簱鎸夐鍩熷垝鍒嗭紙auth銆乮nterview銆乯obs銆乺esume锛夛紝鍚勮嚜鐙珛
- **API 瀹㈡埛绔細** 鍩轰簬 Axios 鐨勯泦涓紡瀹㈡埛绔紝浣嶄簬 `src/api/client.js`锛屼唬鐞?`/api` 鍒板悗绔?8005
- **璁よ瘉锛?* 鎵嬫満鍙?+ 瀵嗙爜锛屽己鍒剁櫥褰曪紙鏈櫥褰曡嚜鍔ㄨ烦杞?`/auth`锛夛紝鏁版嵁蹇呴』瀛?Supabase

## 甯哥敤鍛戒护

```bash
# 鍚庣锛堟帹鑽愮敤 uvicorn锛屾敮鎸佺儹鏇存柊锛?cd backend && python -m uvicorn main:app --host 0.0.0.0 --port 8005 --reload

# 鍓嶇
cd frontend && npm run dev    # 绔彛 5173
```

## 鐜鍙橀噺锛坆ackend/.env锛?
| 鍙橀噺 | 璇存槑 |
|------|------|
| `DEEPSEEK_API_KEY` | DeepSeek 瀹樻柟 API Key锛圴4 Pro 涓绘ā鍨嬶級 |
| `DEEPSEEK_API_URL` | DeepSeek API 鍦板潃 |
| `DEEPSEEK_FLASH_KEY` | 纭呭熀娴佸姩 API Key锛圴3 澶囩敤妯″瀷锛?|
| `DEEPSEEK_FLASH_URL` | 纭呭熀娴佸姩 API 鍦板潃 |
| `DEEPSEEK_FLASH_MODEL` | 澶囩敤妯″瀷鍚嶇О |
| `API_SECRET_KEY` | JWT 绛惧悕瀵嗛挜 |
| `SUPABASE_URL` | Supabase 椤圭洰 URL |
| `SUPABASE_SERVICE_KEY` | Supabase Service Role Key |

## 鏁版嵁搴撹〃锛圫upabase锛?
| 琛?| 鐢ㄩ€?| 鍏抽敭瀛楁 |
|----|------|---------|
| `users_data` | 鐢ㄦ埛琛?| phone, nickname, email, avatar, hashed_password |
| `resume_history` | 绠€鍘嗗垎鏋愬巻鍙?| user_phone, job_title, match_score, keywords, reconstructed_resume |
| `interview_history` | 闈㈣瘯鍘嗗彶 | user_phone, job_type, questions, answers, scores, total_score, advice |
| `jobs` | 宀椾綅鏁版嵁 | title, category, education, female_friendly |
| `tips` | 姹傝亴鎻愮ず | content |

## AI 鍔熻兘

- **鍙屾ā鍨嬪鐏撅細** 鍏堣皟 DeepSeek V4 Pro锛?0s 瓒呮椂锛夛紝澶辫触鑷姩鍒囩鍩烘祦鍔?V3
- **闄嶇骇鏂规锛?* 涓や釜妯″瀷閮藉け璐ユ椂锛岃繑鍥?mock 鏁版嵁锛堝浐瀹氶搴撱€侀殢鏈鸿瘎鍒嗭級
- **闈㈣瘯鍑洪锛?* AI 鏍规嵁宀椾綅绫诲瀷鍔ㄦ€佺敓鎴?5 閬撻
- **闈㈣瘯璇勫垎锛?* 5 缁村害鐪熷疄璇勪及锛堝唴瀹瑰畬鏁存€с€侀€昏緫娓呮櫚搴︺€佷笓涓氭繁搴︺€佽〃杈剧粨鏋勫寲銆佸矖浣嶅尮閰嶅害锛?- **绠€鍘嗗垎鏋愶細** 鎻愬彇 JD 鍏抽敭璇嶏紝涓庣畝鍘嗗尮閰嶏紝鐢熸垚浼樺寲寤鸿

## 鏈€杩戞敼鍔紙鎴嚦 2026-05-22锛?
- 鉁?鍙屾ā鍨嬪鐏撅紙Pro + 纭呭熀娴佸姩 Flash锛?- 鉁?绠€鍘嗘敮鎸?PDF/Word 涓婁紶 + 绮樿创鏂囨湰
- 鉁?闈㈣瘯璇勫垎浠庡亣寰〃鎯呮敼涓?5 缁村害鐪熷疄璇勪及
- 鉁?寮哄埗鐧诲綍锛堟湭鐧诲綍鑷姩璺宠浆锛?- 鉁?澶村儚涓婁紶鍔熻兘锛坆ase64 瀛?Supabase锛?- 鉁?浠婃棩鎻愮ず鏀逛负娓告垙椋庢牸闈㈣瘯鏀荤暐
- 鉁?棣栭〉鍘绘帀缁熻鏁版嵁锛堝彧淇濈暀鍦ㄤ釜浜轰腑蹇冿級
- 鉁?缁熻鏁版嵁浠?Supabase 鏌ヨ鐪熷疄鏁版嵁
- 鉁?淇鍒锋柊鍚庢樉绀?鏈櫥褰?鐨?bug锛圓pp.vue 鍔?fetchUser锛?
## 褰撳墠寰呭仛

- 绠€鍘?闈㈣瘯鍘嗗彶璇︽儏椤碉紙鐩墠鍙脊 alert锛?- 姹傝亴绀剧兢鍔熻兘锛堢洰鍓嶅脊"寮€鍙戜腑"锛?- 閮ㄧ讲涓婄嚎

