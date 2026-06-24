def get_feedback_and_recommendations(profile):
    """
    Generates personalized recommendations, roadmap milestones, and project ideas
    based on the student's profile.
    
    Profile dict structure:
    {
        'cgpa': float,
        'internships': int,
        'projects': int,
        'backlogs': int,
        'coding_score': int,
        'comm_score': int,
        'dsa_score': int,
        'webdev_score': int
    }
    """
    cgpa = float(profile.get('cgpa', 0.0) or 0.0)
    internships = int(profile.get('internships', 0) or 0)
    projects = int(profile.get('projects', 0) or 0)
    backlogs = int(profile.get('backlogs', 0) or 0)
    coding = int(profile.get('coding_score', 0) or 0)
    comm = int(profile.get('comm_score', 0) or 0)
    dsa = int(profile.get('dsa_score', 0) or 0)
    webdev = int(profile.get('webdev_score', 0) or 0)

    feedback = {}
    recommendations = []
    roadmap = []
    project_ideas = []

    # 1. Evaluate Metrics for Status Feedback
    # CGPA
    if cgpa >= 8.5:
        feedback['cgpa'] = {'status': 'Excellent', 'class': 'success', 'desc': 'Your CGPA is outstanding and will easily clear all company cut-offs.'}
    elif cgpa >= 7.0:
        feedback['cgpa'] = {'status': 'Good', 'class': 'warning', 'desc': 'Your CGPA is decent, clearing most cut-offs. Aim to raise it above 7.5 to be fully safe.'}
    else:
        feedback['cgpa'] = {'status': 'Critical', 'class': 'danger', 'desc': 'Below 7.0 is a major barrier. Many top product/service companies require 7.0+ or 7.5+.'}

    # Backlogs
    if backlogs == 0:
        feedback['backlogs'] = {'status': 'Clear', 'class': 'success', 'desc': 'No active backlogs. Perfect.'}
    elif backlogs <= 2:
        feedback['backlogs'] = {'status': 'Warning', 'class': 'warning', 'desc': 'Active backlogs can disqualify you. Clear them in the next available supplementary exam.'}
    else:
        feedback['backlogs'] = {'status': 'Critical', 'class': 'danger', 'desc': 'Multiple active backlogs. Most placement cells will block your registration. Clear these first.'}

    # Coding & DSA
    coding_avg = (coding + dsa) / 2.0
    if coding_avg >= 80:
        feedback['technical'] = {'status': 'Expert', 'class': 'success', 'desc': 'Strong DSA and programming foundations. Ready for high-paying product role interviews.'}
    elif coding_avg >= 50:
        feedback['technical'] = {'status': 'Intermediate', 'class': 'warning', 'desc': 'Decent fundamentals, but needs practice on advanced algorithms and speed.'}
    else:
        feedback['technical'] = {'status': 'Beginner', 'class': 'danger', 'desc': 'Weak technical base. DSA coding tests are the first round in 90% of recruitment drives.'}

    # Projects & Internships
    exp_score = projects + (internships * 1.5)
    if exp_score >= 3.5:
        feedback['experience'] = {'status': 'Strong', 'class': 'success', 'desc': 'Great project portfolio and internship experience. Perfect resume highlights.'}
    elif exp_score >= 1.5:
        feedback['experience'] = {'status': 'Moderate', 'class': 'warning', 'desc': 'Have projects, but lacking real-world internship exposure or complex system builds.'}
    else:
        feedback['experience'] = {'status': 'Weak', 'class': 'danger', 'desc': 'Barren resume. You need to build high-quality projects to stand out in interviews.'}

    # Communication
    if comm >= 75:
        feedback['communication'] = {'status': 'Excellent', 'class': 'success', 'desc': 'Great communication skills. You will clear HR rounds and panel discussions comfortably.'}
    elif comm >= 50:
        feedback['communication'] = {'status': 'Average', 'class': 'warning', 'desc': 'Understandable, but might lack confidence or clear structuring in technical explanation.'}
    else:
        feedback['communication'] = {'status': 'Needs Improvement', 'class': 'danger', 'desc': 'Weak expression. Communication gaps lead to rejection even if technical scores are good.'}

    # 2. Prioritized Recommendations
    # Critical fixes first
    if backlogs > 0:
        recommendations.append({
            'title': 'Clear Active Backlogs',
            'desc': 'Prepare intensely for backlog exams. Most companies require 0 active backlogs at the time of recruitment.',
            'priority': 'Critical',
            'category': 'Academic'
        })
    
    if cgpa < 7.0:
        recommendations.append({
            'title': 'Boost Academic Performance',
            'desc': 'Focus on clearing subjects with high grades in the next semesters. Aim for a minimum semester GPA of 8.0 to pull up your cumulative CGPA.',
            'priority': 'High',
            'category': 'Academic'
        })

    if coding < 50 or dsa < 50:
        recommendations.append({
            'title': 'Strengthen Core DSA foundations',
            'desc': 'Start learning Data Structures (Arrays, Linked Lists, Stacks, Queues) and fundamental Algorithms (Sorting, Binary Search). Practice daily.',
            'priority': 'High',
            'category': 'Technical'
        })

    if projects == 0:
        recommendations.append({
            'title': 'Build a Full-Stack Project',
            'desc': 'Create an end-to-end web or mobile application. Front-end without back-end doesn\'t hold weight during standard tech interviews.',
            'priority': 'High',
            'category': 'Projects'
        })

    if coding_avg >= 50 and coding_avg < 80:
        recommendations.append({
            'title': 'Solve Medium/Hard LeetCode Problems',
            'desc': 'Elevate your problem-solving. Practice Recursion, Trees, Graphs, Hashing, and Dynamic Programming. Aim for 150+ solved problems.',
            'priority': 'Medium',
            'category': 'Technical'
        })

    if internships == 0:
        recommendations.append({
            'title': 'Apply for Internships or Virtual Work Programs',
            'desc': 'Look for startup internships on platforms like Internshala, Wellfound, or LinkedIn. Alternatively, complete a Forage virtual experience program.',
            'priority': 'Medium',
            'category': 'Experience'
        })

    if comm < 60:
        recommendations.append({
            'title': 'Engage in Mock Interviews & Speak Out Loud',
            'desc': 'Practice explaining your code aloud while solving. Record yourself answering HR questions (e.g. "Tell me about yourself") to reduce filler words.',
            'priority': 'High',
            'category': 'Communication'
        })
        
    if webdev < 50 and coding_avg >= 50:
        recommendations.append({
            'title': 'Learn a Modern Tech Stack',
            'desc': 'Gain proficiency in a specialized stack like MERN (MongoDB, Express, React, Node) or Python-Flask/Django + JS to stand out as a developer.',
            'priority': 'Medium',
            'category': 'Development'
        })

    # Default recommendations if profile is already very strong
    if not recommendations:
        recommendations.append({
            'title': 'Refine System Design & Competitive Coding',
            'desc': 'Participate in Leetcode weekly contests and study basic System Design concepts (Caching, Load Balancing, Database Sharding).',
            'priority': 'Low',
            'category': 'Advanced'
        })
        recommendations.append({
            'title': 'Polishing Resume & LinkedIn Profile',
            'desc': 'Ensure your resume uses the STAR method (Situation, Task, Action, Result) for projects. Get peer reviews and optimize your LinkedIn.',
            'priority': 'Low',
            'category': 'Professional'
        })

    # 3. Dynamic Roadmap Generation
    if coding_avg < 50:
        # Beginner Roadmap
        roadmap = [
            {
                'phase': 'Phase 1: Basics (Weeks 1-3)',
                'goal': 'Learn language syntax (Java/Python/C++) and Basic Recursion.',
                'resources': 'W3Schools, FreeCodeCamp, GeeksforGeeks Basic Programming.'
            },
            {
                'phase': 'Phase 2: Core Data Structures (Weeks 4-7)',
                'goal': 'Master Arrays, Linked Lists, Stacks, Queues, and String manipulation.',
                'resources': 'Kunal Kushwaha Java/DSA playlist (YouTube) or NeetCode Beginners.'
            },
            {
                'phase': 'Phase 3: Basic Web Dev & Project (Weeks 8-10)',
                'goal': 'Build a simple web app (HTML, CSS, JS) integrating a free API.',
                'resources': 'The Odin Project or MDN Web Docs.'
            },
            {
                'phase': 'Phase 4: Placement Readiness (Weeks 11-12)',
                'goal': 'Solve 50 easy LeetCode problems and create a standard 1-page resume.',
                'resources': 'LeetCode Top Interview 150 (Easy filter), Overleaf standard LaTeX resume templates.'
            }
        ]
    elif coding_avg < 80:
        # Intermediate Roadmap
        roadmap = [
            {
                'phase': 'Phase 1: Intermediate DSA (Weeks 1-3)',
                'goal': 'Master Trees, BST, Graphs, DFS/BFS, and HashMaps.',
                'resources': 'Striver\'s A-Z DSA Course, NeetCode 150 roadmap.'
            },
            {
                'phase': 'Phase 2: Database & System Fundamentals (Weeks 4-6)',
                'goal': 'Learn SQL queries, Database Normalization, and Operating Systems (OS) basics like Process Scheduling.',
                'resources': 'Gate Smashers (YouTube) or InterviewBit OS Tutorial.'
            },
            {
                'phase': 'Phase 3: Advanced Development Project (Weeks 7-9)',
                'goal': 'Build a full-stack CRUD application with authentication (JWT) and database (MongoDB/PostgreSQL).',
                'resources': 'FullStackOpen (University of Helsinki) or Traversy Media.'
            },
            {
                'phase': 'Phase 4: Mock Tests & HR Prep (Weeks 10-12)',
                'goal': 'Take timed aptitude tests, mock technical interviews, and clear object-oriented design principles (OOPs).',
                'resources': 'IndiaBIX for Aptitude, Pramp/Interviewing.io for mock interviews.'
            }
        ]
    else:
        # Advanced Roadmap
        roadmap = [
            {
                'phase': 'Phase 1: Competitive Programming & Contests (Weeks 1-4)',
                'goal': 'Participate in LeetCode/Codeforces contests weekly. Solve hard Dynamic Programming & Graph queries.',
                'resources': 'LeetCode Weekly Contests, USACO Guide.'
            },
            {
                'phase': 'Phase 2: System Design & Architecture (Weeks 5-8)',
                'goal': 'Understand Horizontal scaling, Microservices, Caching mechanisms, and Message Queues (Kafka).',
                'resources': 'ByteByteGo (Alex Xu) System Design primer, Gaurav Sen (YouTube).'
            },
            {
                'phase': 'Phase 3: Open Source & Resume Polish (Weeks 9-10)',
                'goal': 'Contribute to open-source software, write a tech blog post about your projects, and optimize resume details.',
                'resources': 'First Contributions on GitHub, GitHub Explore.'
            },
            {
                'phase': 'Phase 4: High-Tier Negotiation & Mock Interviews (Weeks 11-12)',
                'goal': 'Behavioral interview prep using the STAR method, and practicing mock salary negotiations.',
                'resources': 'Tech Interview Handbook, CareerCup.'
            }
        ]

    # 4. Tailored Project Ideas
    # Choose projects based on skill focus
    if webdev < 60:
        project_ideas.append({
            'title': 'Personal Finance Tracker Dashboard',
            'desc': 'A sleek, glassmorphic financial tracker where users can input expenses, categorize them, and see dynamic visualizations (pie charts) of their monthly budget.',
            'stack': 'HTML5, Vanilla CSS, JS (Chart.js), LocalStorage or Node/Express backend',
            'difficulty': 'Beginner-Intermediate'
        })
        project_ideas.append({
            'title': 'Job Application Tracker (Kanban Board)',
            'desc': 'A board layout application that allows students to track job applications (Applied, Interviewing, Offered, Rejected) with drag-and-drop capability and interview reminder dates.',
            'stack': 'React.js, CSS Modules, Firebase for real-time Auth/DB',
            'difficulty': 'Intermediate'
        })
    else:
        project_ideas.append({
            'title': 'Collaborative Real-time Code Editor',
            'desc': 'A web-based IDE that lets multiple users collaborate on code simultaneously. Features syntax highlighting, chat room, and a compiling engine.',
            'stack': 'React, WebSockets (Socket.io), Node.js, Express, Docker (for code sandboxing)',
            'difficulty': 'Advanced'
        })
        project_ideas.append({
            'title': 'AI-Powered Resume Screen & Feedback Agent',
            'desc': 'An application that uploads PDF resumes, extracts text, matches it against a given job description using TF-IDF or embedding cosine similarity, and highlights missing keywords.',
            'stack': 'Python, Flask/FastAPI, PyPDF2, Scikit-Learn (TF-IDF), Chart.js frontend',
            'difficulty': 'Intermediate-Advanced'
        })

    # Add a generic project if lists are short
    if len(project_ideas) < 2:
        project_ideas.append({
            'title': 'Secure File-Sharing Cloud Portal',
            'desc': 'A platform to upload, download, and share files securely with time-limited links and password protection.',
            'stack': 'Node.js, Express, AWS S3 / Cloudinary, JWT Authentication, React.js',
            'difficulty': 'Intermediate'
        })

    return {
        'feedback': feedback,
        'recommendations': recommendations,
        'roadmap': roadmap,
        'project_ideas': project_ideas
    }
