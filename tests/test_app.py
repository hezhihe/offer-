from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 390, "height": 844})
    page.goto('http://localhost:8080/')
    page.wait_for_load_state('networkidle')
    time.sleep(1)

    page.screenshot(path='c:/Users/LEGION/Desktop/26.5.8 offer罗盘/test_home.png', full_page=True)
    print("1. Home page screenshot taken")

    page.locator('.nav-item', has_text='简历').click()
    time.sleep(0.5)
    page.screenshot(path='c:/Users/LEGION/Desktop/26.5.8 offer罗盘/test_resume.png', full_page=True)
    print("2. Resume page screenshot taken")

    page.locator('button:has-text("填充示例")').click()
    time.sleep(0.5)
    page.screenshot(path='c:/Users/LEGION/Desktop/26.5.8 offer罗盘/test_resume_filled.png', full_page=True)
    print("3. Resume with sample data screenshot taken")

    page.locator('button:has-text("开始重构")').click()
    time.sleep(2.5)
    page.screenshot(path='c:/Users/LEGION/Desktop/26.5.8 offer罗盘/test_resume_result.png', full_page=True)
    print("4. Resume analysis result screenshot taken")

    page.locator('.nav-item', has_text='面试').click()
    time.sleep(0.5)
    page.screenshot(path='c:/Users/LEGION/Desktop/26.5.8 offer罗盘/test_interview.png', full_page=True)
    print("5. Interview page screenshot taken")

    page.locator('.job-card', has_text='AI算法工程师').click()
    time.sleep(1)
    page.screenshot(path='c:/Users/LEGION/Desktop/26.5.8 offer罗盘/test_interview_active.png', full_page=True)
    print("6. Interview active screenshot taken")

    page.locator('#answerInput').fill('Transformer是一种基于自注意力机制的深度学习架构，它通过计算序列中每个位置与其他所有位置的关系来捕捉全局依赖。Self-Attention通过Query、Key、Value三个矩阵计算注意力权重，从而实现并行化的序列建模。')
    page.locator('button:has-text("发送")').click()
    time.sleep(2)
    page.screenshot(path='c:/Users/LEGION/Desktop/26.5.8 offer罗盘/test_interview_feedback.png', full_page=True)
    print("7. Interview feedback screenshot taken")

    page.locator('.nav-item', has_text='日历').click()
    time.sleep(0.5)
    page.screenshot(path='c:/Users/LEGION/Desktop/26.5.8 offer罗盘/test_calendar.png', full_page=True)
    print("8. Calendar list view screenshot taken")

    page.locator('button:has-text("日历")').click()
    time.sleep(0.5)
    page.screenshot(path='c:/Users/LEGION/Desktop/26.5.8 offer罗盘/test_calendar_grid.png', full_page=True)
    print("9. Calendar grid view screenshot taken")

    page.locator('.nav-item', has_text='我的').click()
    time.sleep(0.5)
    page.screenshot(path='c:/Users/LEGION/Desktop/26.5.8 offer罗盘/test_profile.png', full_page=True)
    print("10. Profile page screenshot taken")

    browser.close()
    print("\nAll tests completed successfully!")
