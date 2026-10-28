import React from "react";
import { Link } from "react-router-dom";
import { useTitle } from "../hooks/useTitle";
import styles from "../CSSModules/base.module.css";

const cards = [
    {
        title: "Preparation Exam",
        description: "Personalize your experience and track progress with a placement exam.",
        color: "blue",
        icon: "?",
        to: "/prep_exam"
    },
    {
        title: "Practice Problems",
        description: "Work through problem sets tailored to your course.",
        color: "orange",
        icon: "✎",
        to: "/practice"
    },
    {
        title: "Study Guides",
        description: "Browse topic summaries and formula sheets.",
        color: "green",
        icon: "📘",
        to: "/study"
    },
    {
        title: "Past Sessions",
        description: "Review your tutoring history and saved answers.",
        color: "red",
        icon: "↻",
        to: "/past"
    },
];

const Home: React.FC = () => {
    useTitle("Home | Chem Tutor");

    return (
        <div className={`${styles.page} content`}>
            <div className={styles.pageIntro}>
                <h1>Welcome to your Chemistry Tutor</h1>
                <p>Pick up where you left off, or start something new.</p>
            </div>

            <div className="dashboardGrid">
                {cards.map((card) => (
                    <Link
                        className="card"
                        key={card.title}
                        to={card.to}>
                    <div className={`cardIcon ${card.color}`}>{card.icon}</div>
                    <h3>{card.title}</h3>
                    <p>{card.description}</p>
                    </Link>
                ))}
            </div>
        </div>
    );
};

export default Home;