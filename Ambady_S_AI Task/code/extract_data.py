import pdfplumber
import os
import re
import pandas as pd
from collections import defaultdict

# Function to extract text from PDF files
def extract_text_from_pdf(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text()
    return text

# Function to extract name, email, and mobile number
def extract_name_email_mobile(text):
    name = "N/A"
    email = "N/A"
    mobile = "N/A"
    
    # Refined name extraction: Target common resume structures
    name_match = re.search(r"([A-Z][a-z]+\s[A-Z][a-z]+|[A-Z][a-z]+(?:\s[A-Z][a-z]+)+)", text)
    if name_match:
        name = name_match.group(0).strip()
    
    # Extract email
    emails = re.findall(r'\S+@\S+', text)
    if emails:
        email = emails[0]
    
    # Extract mobile number
    mobile_match = re.findall(r"\(?\+?\d{1,4}\)?[-.\s]?\(?\d{1,3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", text)
    if mobile_match:
        mobile = mobile_match[0]
    
    return name, f"{email} | {mobile}"

# Function to extract key skills based on a predefined list
def extract_key_skills(text):
    skills_keywords = [
        "Python", "Java", "C++", "TensorFlow", "Docker", "Kubernetes", "Machine Learning", "AI", "SQL", 
        "R", "Deep Learning", "C", "Go", "Ruby", "Rust", "Kotlin", "PHP", "TypeScript", "Perl", "MATLAB", 
        "React.js", "Angular", "Vue.js", "Spring", "Django", "Flask", "AWS", "Azure", "Google Cloud",
        "OpenCV", "NumPy", "Pandas", "BERT", "GPT", "Transformers", "NLTK", "Neural Networks", "Data Science"
    ]
    skills_found = [skill for skill in skills_keywords if skill.lower() in text.lower()]
    return ", ".join(skills_found)

# Function to extract course and discipline
def extract_course_and_discipline(text):
    course = "N/A"
    discipline = "N/A"
    
    # Match courses like BTech, B.Sc, etc.
    course_pattern = re.search(r"\b(BTech|B\.Tech|BSc|B\.Sc|MTech|M\.Tech|MCA|BCA|MBA|BA|BArch|B\.Arch)\b", text, re.IGNORECASE)
    if course_pattern:
        course = course_pattern.group(0).replace(".", "")
    
    # Define a list of recognized disciplines and their variations
    disciplines_dict = {
        "Computer Science": ["Computer Science", "CS", "CSE", "Information Technology", "IT", "Software Engineering"],
        "Data Science": ["Data Science", "Big Data", "Data Analytics", "Data Engineering", "Business Analytics"],
        "Artificial Intelligence": ["AI", "Artificial Intelligence", "Machine Learning", "Deep Learning", "Neural Networks", "ML"],
        "Robotics": ["Robotics", "Robotic Engineering", "Automation", "Mechatronics", "AI Robotics"],
        "Architecture": ["Architecture", "Sustainable Design", "Urban Planning"],
        "Electrical Engineering": ["Electrical Engineering", "EEE", "Electrical", "Electronics", "Microelectronics", "Power Systems", "Electrical Engineering"],
        "Mechanical Engineering": ["Mechanical Engineering", "Mechanical", "ME", "Manufacturing", "Production Engineering"],
        "Civil Engineering": ["Civil Engineering", "CE", "Structural Engineering", "Construction Engineering"],
        "Chemical Engineering": ["Chemical Engineering", "ChemE"],
        "Biomedical Engineering": ["Biomedical Engineering", "BME", "Biomedical", "Biotechnology", "Biomaterials", "Healthcare Engineering"],
        "Management": ["Management", "Business Administration", "MBA"],
        "Mathematics": ["Mathematics", "Applied Mathematics", "Pure Mathematics"],
        "Electronics Engineering": ["Electronics Engineering", "Electronics", "ECE", "VLSI", "Embedded Systems"]
    }
    
    for discipline, keywords in disciplines_dict.items():
        for keyword in keywords:
            if re.search(r"\b" + re.escape(keyword) + r"\b", text, re.IGNORECASE):
                return course, discipline
    
    return course, "Unidentified Discipline"

# Function to extract CGPA or percentage
def extract_cgpa_percentage(text):
    cgpa_match = re.search(r"(CGPA|GPA|Percentage)\s*[:\-]?\s*([\d.]+(?:/\d+)?|\d{1,2}\.\d+)", text, re.IGNORECASE)
    if cgpa_match:
        return cgpa_match.group(2)
    return "N/A"

# Function to extract experience scores with more accurate scoring
def extract_experience_score(text, category):
    score = 1  # Default score: Exposed
    experience_keywords = {
        "gen ai": [
            ("generative", 1), 
            ("transformers", 2), 
            ("GPT", 2), 
            ("BERT", 2), 
            ("large language models", 2), 
            ("RAG", 3), 
            ("evaluations", 3), 
            ("agentic", 3),
            ("deep learning", 2),  # Added to reflect the general experience with deep learning
        ],
        "ai/ml": [
            ("machine learning", 2), 
            ("deep learning", 2), 
            ("AI", 1), 
            ("neural networks", 2), 
            ("hands-on", 2),
            ("advanced", 3), 
            ("computer vision", 3),
            ("NLP", 3),
            ("data science", 2),
            ("reinforcement learning", 3),  # Added more advanced topics
            ("natural language processing", 3)  # Included NLP as an advanced area
        ]
    }

    # Extract the category-specific keywords
    keywords = experience_keywords.get(category.lower(), [])

    # Track keyword hits with weights
    weighted_score = 0
    keyword_hits = 0
    
    for keyword, weight in keywords:
        keyword_count = len(re.findall(rf"\b{re.escape(keyword)}\b", text.lower()))
        
        if keyword_count > 0:
            weighted_score += weight * keyword_count  # Add weight for each keyword occurrence
            keyword_hits += 1

    # Determine score based on the weighted keyword hits
    if weighted_score > 15:  # High experience
        score = 3
    elif weighted_score > 5:  # Moderate experience
        score = 2
    else:  # Low exposure
        score = 1
    
    return score

# Function to extract detailed supporting information
def extract_supporting_info(text):
    info = []
    info_categories = {
        "Certifications": r"(certifications?.*?:?.*?(?:\n|$))",
        "Internships": r"(internships?.*?:?.*?(?:\n|$))",
        "Projects": r"(projects?.*?:?.*?(?:\n|$))",
        "Awards": r"(awards?.*?:?.*?(?:\n|$))",
        "Volunteer": r"(volunteer.*?:?.*?(?:\n|$))"
    }
    
    for category, pattern in info_categories.items():
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            info.append(f"{category}: {', '.join(match.strip() for match in matches)}")

    return "\n".join(info) if info else "N/A"

# Function to extract university and year of study
def extract_university_and_year(text):
    university = "N/A"
    year_of_study = "N/A"
    
    # Match university names
    university_pattern = re.search(r"(University|Institute of Technology|College|School of Engineering|Academy|Institute)[^\n]*", text, re.IGNORECASE)
    if university_pattern:
        university = university_pattern.group(0).strip()
    
    # Match valid 4-digit years (e.g., 2020, 2021) for possible years of study or graduation year
    year_matches = re.findall(r"\b(20[0-9]{2})\b", text)  # Look for years in the 2000-2099 range
    if year_matches:
        # Try to identify year of study based on proximity to course names or other terms
        for year in year_matches:
            if int(year) >= 2019:  # Consider it within study years
                year_of_study = year
                break

    return university, year_of_study

# Function to process resumes and extract information
def process_resumes(input_folder, output_file):
    data = defaultdict(list)
    for filename in os.listdir(input_folder):
        if filename.endswith(".pdf"):
            pdf_path = os.path.join(input_folder, filename)
            print(f"Processing {filename}...")

            try:
                text = extract_text_from_pdf(pdf_path)
                name, contact_details = extract_name_email_mobile(text)
                key_skills = extract_key_skills(text)
                course, discipline = extract_course_and_discipline(text)
                cgpa = extract_cgpa_percentage(text)
                gen_ai_score = extract_experience_score(text, "gen ai")
                ai_ml_score = extract_experience_score(text, "ai/ml")
                supporting_info = extract_supporting_info(text)
                university, year_of_study = extract_university_and_year(text)

                # Append extracted data
                data['Name'].append(name)
                data['Contact Details'].append(contact_details)
                data['University'].append(university)
                data['Year of Study'].append(year_of_study)
                data['Course'].append(course)
                data['Discipline'].append(discipline)
                data['CGPA/Percentage'].append(cgpa)
                data['Key Skills'].append(key_skills)
                data['Gen AI Experience Score'].append(gen_ai_score)
                data['AI/ML Experience Score'].append(ai_ml_score)
                data['Supporting Information'].append(supporting_info)
            except Exception as e:
                print(f"Error processing {filename}: {e}")
    
    # Create DataFrame from extracted data
    df = pd.DataFrame(data)

    # Calculate Total Score and Rank
    df['Total Score'] = df['Gen AI Experience Score'] + df['AI/ML Experience Score']
    df['Ranking'] = df['Total Score'].rank(ascending=False, method='dense').astype(int)

    # Save DataFrame to Excel
    df.to_excel(output_file, index=False)
    print(f"Processing complete. Results saved to {output_file}")

# Example usage
input_folder = r"C:\Users\ambad\OneDrive\Documents\AI Projects\Ambady_S_AI Task\resumes"
output_file = r"C:\Users\ambad\OneDrive\Documents\AI Projects\Ambady_S_AI Task\output\resumes_info.xlsx"
process_resumes(input_folder, output_file)

#demo!