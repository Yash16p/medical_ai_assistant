import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from tools.patient_db import PatientDB

def display_patient(patient):
    """Display patient information in a readable format"""
    if not patient:
        print("Patient not found.")
        return
    
    print(f"\n{'='*60}")
    print(f"Patient ID: {patient[1]}")
    print(f"Name: {patient[2]}")
    print(f"Age: {patient[3]} years old")
    print(f"Gender: {patient[4]}")
    print(f"Date Admitted: {patient[10]}")
    print(f"\nDiagnosis: {patient[5]}")
    print(f"\nSymptoms: {patient[6]}")
    print(f"\nLab Results: {patient[7]}")
    print(f"\nTreatment Plan: {patient[8]}")
    print(f"\nMedications: {patient[9]}")
    print(f"\nDoctor Notes: {patient[11]}")
    print(f"{'='*60}")

def main():
    db = PatientDB()
    
    while True:
        print("\n" + "="*50)
        print("NEPHROLOGY PATIENT DATABASE")
        print("="*50)
        print("1. View all patients (summary)")
        print("2. Search patient by ID")
        print("3. Search patients by keyword")
        print("4. View patient details")
        print("5. Database statistics")
        print("6. Exit")
        
        choice = input("\nEnter your choice (1-6): ").strip()
        
        if choice == "1":
            patients = db.get_all_patients()
            if not patients:
                print("No patients found in database.")
                continue
            
            print(f"\nFound {len(patients)} patients:")
            print(f"{'ID':<8} {'Name':<20} {'Age':<5} {'Diagnosis':<30}")
            print("-" * 70)
            for patient in patients:
                print(f"{patient[1]:<8} {patient[2]:<20} {patient[3]:<5} {patient[5]:<30}")
        
        elif choice == "2":
            patient_id = input("Enter patient ID: ").strip()
            patient = db.get_patient(patient_id)
            display_patient(patient)
        
        elif choice == "3":
            keyword = input("Enter search keyword: ").strip()
            patients = db.search_patients(keyword)
            if not patients:
                print("No patients found matching your search.")
                continue
            
            print(f"\nFound {len(patients)} patients matching '{keyword}':")
            print(f"{'ID':<8} {'Name':<20} {'Age':<5} {'Diagnosis':<30}")
            print("-" * 70)
            for patient in patients:
                print(f"{patient[1]:<8} {patient[2]:<20} {patient[3]:<5} {patient[5]:<30}")
        
        elif choice == "4":
            patient_id = input("Enter patient ID for detailed view: ").strip()
            patient = db.get_patient(patient_id)
            display_patient(patient)
        
        elif choice == "5":
            patients = db.get_all_patients()
            print(f"\nDatabase Statistics:")
            print(f"Total patients: {len(patients)}")
            
            if patients:
                # Age statistics
                ages = [p[3] for p in patients]
                print(f"Average age: {sum(ages)/len(ages):.1f} years")
                print(f"Age range: {min(ages)} - {max(ages)} years")
                
                # Gender distribution
                genders = [p[4] for p in patients]
                male_count = genders.count("Male")
                female_count = genders.count("Female")
                print(f"Gender distribution: {male_count} Male, {female_count} Female")
                
                # Most common diagnoses
                diagnoses = [p[5] for p in patients]
                diagnosis_counts = {}
                for d in diagnoses:
                    diagnosis_counts[d] = diagnosis_counts.get(d, 0) + 1
                
                print(f"\nMost common diagnoses:")
                sorted_diagnoses = sorted(diagnosis_counts.items(), key=lambda x: x[1], reverse=True)
                for diagnosis, count in sorted_diagnoses[:5]:
                    print(f"  {diagnosis}: {count} patients")
        
        elif choice == "6":
            print("Goodbye!")
            break
        
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()