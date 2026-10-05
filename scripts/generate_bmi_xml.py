print('    <url>')
print('        <loc>https://makuistudio.com/tools/bmi-by-height.html</loc>;')
print('        <lastmod>2026-10-05</lastmod>')
print('        <changefreq>monthly</changefreq>')
print('        <priority>0.8</priority>')
print('    </url>')
for total_in in range(60, 77):
    ft = total_in // 12
    inch = total_in % 12
    print('    <url>')
    print(f'        <loc>https://makuistudio.com/tools/bmi-{ft}-ft-{inch}.html</loc>')
    print('        <lastmod>2026-10-05</lastmod>')
    print('        <changefreq>monthly</changefreq>')
    print('        <priority>0.7</priority>')
    print('    </url>')