export interface ClassInfo {
    id: number;
    type: 'lab' | 'lecture';
    code: string;
    title: string;
    level: 100 | 200 | 300 | 400 | 500;
}

export const requiredClasses: ClassInfo[] = [
    {id:1, type: 'lecture', code: 'CHEM 111', title: 'Principles of Chemistry 1', level: 100 },
    {id:2, type: 'lecture', code: 'CHEM 112', title: 'Principles of Chemistry 2', level: 100 },
    {id:3, type: 'lab', code: 'CHEM 113', title: 'Intro General Chemistry Lab', level: 100 },
    {id:4, type: 'lab', code: 'CHEM 201', title: 'Chem Handling & Safe Lab Prac', level: 200 },
    {id:5, type: 'lecture', code: 'CHEM 227', title: 'Principles of Chem Analysis', level: 200 },
    {id:6, type: 'lecture', code: 'CHEM 351M', title: 'Organic Chemistry 1', level: 300 },
    {id:7, type: 'lecture', code: 'CHEM 352M', title: 'Organic Chemistry 2', level: 300 },
    {id:8, type: 'lab', code: 'CHEM 354', title: 'Organic Chem Lab', level: 300 },
    {id:9, type: 'lecture', code: 'CHEM 381M', title: 'Biochem Fundamentals', level: 300 },
    {id:10, type: 'lecture', code: 'CHEM 391', title: 'Tech Writing Using Chem Lit', level: 300 },
    {id:11, type: 'lecture', code: 'CHEM 460', title: 'Math for Physical Chemistry', level: 400 },
    {id:12, type: 'lecture', code: 'CHEM 462', title: 'Physical Chemistry 1', level: 400 },
    {id:13, type: 'lecture', code: 'CHEM 463', title: 'Physical Chemistry 2', level: 400 },
    {id:14, type: 'lab', code: 'CHEM 464', title: 'Physical Chemistry Lab 1', level: 400 },
    {id:15, type: 'lab', code: 'CHEM 465', title: 'Physical Chemistry Lab 2', level: 400 },
    {id:16, type: 'lecture', code: 'CHEM 495', title: 'Senior Seminar', level: 400 },
    {id:17, type: 'lecture', code: 'CHEM 514', title: 'Inorganic Chemistry', level: 500 },
    {id:18, type: 'lab', code: 'CHEM 518', title: 'Advanced Inorganic Laboratory', level: 500 },
    {id:19, type: 'lecture', code: 'CHEM 594R', title: 'General Seminar', level: 500 },
]