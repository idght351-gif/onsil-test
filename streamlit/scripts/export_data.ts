// React 앱의 문제·카테고리 데이터를 Streamlit용 JSON으로 내보냄.
// 실행: npx --prefix app esbuild streamlit/scripts/export_data.ts --bundle --platform=node --outfile=<tmp>.cjs && node <tmp>.cjs
import { writeFileSync } from 'node:fs'
import { join } from 'node:path'
import { QUESTIONS } from '../../app/src/data/questions'
import { CATEGORIES } from '../../app/src/data/categories'

const out = join(process.cwd(), 'streamlit', 'data')
writeFileSync(join(out, 'questions.json'), JSON.stringify(QUESTIONS, null, 2) + '\n', 'utf8')
writeFileSync(join(out, 'categories.json'), JSON.stringify(CATEGORIES, null, 2) + '\n', 'utf8')
console.log(`questions: ${QUESTIONS.length}, categories: ${CATEGORIES.length}`)
