
SERVICE_DATA = {
    # ---- Vocational Services ----
    "Electrical Services": [
        "Electrician",
        "Residential Electrician",
        "Commercial Electrician",
        "Industrial Electrician",
        "Maintenance Electrician",
    ],
    "Plumbing Services": [
        "Plumber",
    ],
    "Carpentry Services": [
        "Carpenter",
        "Furniture Carpenter",
    ],
    "Welding Services": [
        "Welder",
        "Fabricator",
        "Aluminum Welder",
    ],
    "Tiling Services": [
        "Tiler",
    ],
    "POP Ceiling Installation": [
        "POP Ceiling Installer",
    ],
    "Painting Services": [
        "Painter",
    ],
    "Roofing Services": [
        "Roofer",
        "Roof Installer",
    ],
    "Borehole Services": [
        "Borehole Driller",
        "Borehole Technician",
        "Water Treatment Technician",
        "Pump Installer",
    ],
    "CCTV Installation Services": [
        "CCTV Installer",
        "Security Systems Technician",
        "Access Control Installer",
    ],
    "Solar Installation Services": [
        "Solar Installer",
        "Solar Technician",
        "Solar System Designer",
    ],
    "Generator Repair & Maintenance": [
        "Generator Technician",
        "Generator Installer",
        "Generator Maintenance Technician",
    ],
    "HVAC & Refrigeration Services": [
        "HVAC Technician",
        "Air Conditioner Technician",
        "Refrigerator Technician",
    ],
    "Auto Repair & Maintenance": [
        "Auto Mechanic",
        "Auto Electrician",
        "Panel Beater",
        "Auto Painter",
    ],
    "Cleaning Services": [
        "Residential Cleaner",
        "Commercial Cleaner",
        "Deep Cleaning Specialist",
    ],
    "Laundry & Dry Cleaning Services": [
        "Laundry Specialist",
        "Dry Cleaner",
    ],
    "Fumigation & Pest Control Services": [
        "Pest Control Technician",
        "Fumigation Specialist",
    ],
    "Barbering Services": [
        "Barber",
        "Hair Grooming Specialist",
    ],
    "Beauty Services": [
        "Hair Stylist",
        "Makeup Artist",
        "Nail Technician",
        "Lash Technician",
        "Gele Artist",
    ],
    "Spa & Massage Services": [
        "Massage Therapist",
        "Spa Therapist",
        "Skincare Specialist",
        "Esthetician",
    ],
    "Fashion Design & Tailoring": [
        "Fashion Designer",
        "Tailor",
        "Pattern Maker",
        "Garment Maker",
    ],
    "Shoe Making & Repair": [
        "Shoemaker",
        "Cobbler",
        "Leather Craftsman",
    ],
    "Photography & Videography": [
        "Photographer",
        "Event Photographer",
        "Product Photographer",
        "Videographer",
        "Drone Operator",
        "Cinematographer",
    ],
    "Electronics & Appliance Repair": [
        "Electronics Technician",
        "TV Repair Technician",
        "Phone Repair Technician",
        "Laptop Repair Technician",
        "Appliance Repair Technician",
    ],
    "Art & Creative Services": [
        "Artist",
        "Sculptor",
        "Portrait Artist",
    ],
    # ---- Digital Services ----
    "Software Development": [
        "Frontend Developer",
        "Backend Developer",
        "Full Stack Developer",
        "Web Developer",
    ],
    "Mobile App Development": [
        "Mobile Developer",
        "Android Developer",
        "iOS Developer",
        "Flutter Developer",
        "React Native Developer",
    ],
    "AI & Machine Learning Services": [
        "AI Engineer",
        "Machine Learning Engineer",
        "Deep Learning Engineer",
        "NLP Engineer",
    ],
    "DevOps Engineering": [
        "DevOps Engineer",
        "Site Reliability Engineer (Sre)",
        "Platform Engineer",
    ],
    "Cloud Engineering": [
        "Cloud Engineer",
        "Cloud Architect",
        "Cloud Administrator",
    ],
    "Blockchain Development": [
        "Blockchain Developer",
        "Smart Contract Developer",
        "Web3 Developer",
    ],
    "Ui/Ux Design": [
        "Ui/Ux Designer",
        "Product Designer",
        "Interaction Designer",
    ],
    "Graphic Design": [
        "Graphic Designer",
        "Brand Designer",
        "Logo Designer",
        "Print Designer",
    ],
    "Motion Graphics Design": [
        "Motion Designer",
        "Motion Graphics Artist",
    ],
    "Illustration & Animation": [
        "Illustrator",
        "2D Animator",
        "3D Animator",
        "Character Designer",
    ],
    "WordPress Development": [
        "WordPress Developer",
        "WordPress Designer",
        "WooCommerce Developer",
    ],
    "Data Analytics & Business Intelligence": [
        "Data Analyst",
        "Business Intelligence Analyst",
        "Bi Developer",
    ],
    "Data Science": [
        "Data Scientist",
        "Research Scientist",
    ],
    "Data Engineering": [
        "Data Engineer",
        "Etl Developer",
        "Big Data Engineer",
    ],
    "Cybersecurity Services": [
        "Cybersecurity Analyst",
        "Penetration Tester",
        "Security Engineer",
        "Soc Analyst",
        "Ethical Hacker",
    ],
    "IT Support Services": [
        "It Support Specialist",
        "Help Desk Technician",
        "System Administrator",
        "Network Administrator",
    ],
    "Digital Marketing": [
        "Digital Marketer",
        "SEO Specialist",
        "SEM Specialist",
        "PPC Specialist",
        "Email Marketer",
        "Performance Marketer",
    ],
    "Social Media Management": [
        "Social Media Manager",
        "Community Manager",
        "Social Media Strategist",
    ],
    "Content Creation": [
        "Content Creator",
        "AI Content Creator",
        "UGC Creator",
        "Influencer",
    ],
    "Writing Services": [
        "Copywriter",
        "Content Writer",
        "Technical Writer",
        "Ghostwriter",
        "Script Writer",
        "Grant Writer",
        "Cv Writer",
    ],
    "Video & Audio Editing": [
        "Video Editor",
        "Audio Editor",
        "Podcast Editor",
    ],
    "Virtual Assistance": [
        "Virtual Assistant",
    ],
    "Product Management": [
        "Product Manager",
        "Product Owner",
    ],
    "AI Automation Services": [
        "AI Automation Specialist",
        "Prompt Engineer",
        "AI Workflow Engineer",
        "No-Code Automation Specialist",
        "Automation Engineer",
    ],
}

def run():
    keys = []
    values = []
    for key, value in SERVICE_DATA.items():
        for item in value:
            values.append(item)
        keys.append(key)
        

    print("Service Categories:  %s", len(keys))
    print("Services: %s", len(values))

if __name__ == "__main__":
    print(run())
