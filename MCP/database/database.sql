-- Create the database table for questions and answers
CREATE TABLE main (
  id INTEGER PRIMARY KEY, -- Use INTEGER PRIMARY KEY for auto-increment in most dialects (especially SQLite)
  question VARCHAR(5000) NOT NULL, -- Use a large VARCHAR for the question text
  answer VARCHAR(5000) NOT NULL  -- Use a large VARCHAR for the answer text
);

-- Insert the data into the table
-- Note: Single quotes are used for string literals (e.g., 'NTUST').
INSERT INTO main (id, question, answer) VALUES
(1, 'What is NTUST?', 'NTUST, also known as Taiwan Tech, is a public research university in Taipei, Taiwan. Established in 1974, it was the first higher education institution of its kind in Taiwan''s technical and vocational education system.'),
(2, 'Where is NTUST located?', 'NTUST is located at No. 43, Section 4, Keelung Road, Da''an District, Taipei City, Taiwan.'),
(3, 'What are the most popular department in NTUST?', 'Based on recent rankings and citations, some of the most popular and highly-ranked departments at NTUST include: Art and Design, Education and Training, Architecture and Built Environment, and Civil and Structural Engineering. Additionally, core STEM fields like Business and Management, Computer Science, Materials Science, and Electrical Engineering have also shown strong performance.'),
(4, 'Official name', 'National Taiwan University of Science and Technology (NTUST), also Taiwan Tech or TaiwanTech.'),
(5, 'Chinese name', '國立臺灣科技大學 (commonly 臺科大)'),
(6, 'Established', '1974 (established originally as National Taiwan Institute of Technology).'),
(7, 'Main campus location', 'Gongguan Campus, Daan District, Taipei City, Taiwan.'),
(8, 'President (as listed publicly)', 'See NTUST official site or Wikipedia for current president name; this can change over time.'),
(9, 'Student population (approx.)', 'Around 11,600 students total (numbers vary by year; see official stats).'),
(10, 'Major colleges', 'College of Engineering; College of Electrical Engineering and Computer Science; School of Management; College of Design; College of Liberal Arts and Social Sciences; College of Intellectual Property Studies; Honors College.'),
(11, 'Campus type', 'Urban campus, multiple campuses including Gongguan (main) and Huaxia campus (Zhonghe).'),
(12, 'International students', 'NTUST hosts international master''s and doctoral students; it is noted as one of Taiwan''s most popular universities for international students.'),
(13, 'Notable rankings (examples)', 'Ranks in QS subject rankings across multiple subjects; QS Asia ranking and other lists—see NTUST ranking pages for details.'),
(14, 'Research highlights', 'NTUST faculty have been recognized among top scientists; NTUST reports many faculty selected among top 2% globally and various IEEE Fellows.'),
(15, 'Website', 'https://www.ntust.edu.tw/'),
(16, 'Short FAQ: What is NTUST known for?', 'NTUST (Taiwan Tech) is known for engineering, applied sciences, design, industry collaboration, entrepreneurship, and technology licensing.'),
(17, 'School code (Taiwan)', 'School code (MOE listing) 0022 (refer to official MOE data).'),
(18, 'How to find departments', 'Visit https://www.ntust.edu.tw/ and browse ''Academics'' for department and graduate program lists.');