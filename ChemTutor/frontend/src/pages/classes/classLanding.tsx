import { useMemo } from "react";
import { Link } from "react-router-dom";
import styles from '../../CSSModules/classLanding.module.css';
import { requiredClasses, type ClassInfo} from '../../data/classes';
import { scatterBubbles } from "../../utils/classBubbles";
import { useTitle } from "../../hooks/useTitle";

const GROUPS = [
    { key: 'lower', label: '100 & 200 Level', levels: [100, 200]},
    { key: 'mid', label: '300 Level', levels: [300]},
    { key: 'upper', label: '400 & 500 Level', levels: [400, 500]},
] as const;

const BUBBLE_SIZE_PERCENT = 16;

export default function ClassLanding() {
    useTitle("Classes | Chem Tutor")
    const groupedClasses = useMemo(
        () =>
            GROUPS.map((group) => ({
                ...group,
                items: requiredClasses.filter((c) => (group.levels as readonly number[]).includes(c.level)),
            })),
            []
    );

    return (
        <div className={styles.page}>
            <header className={styles.intro}>
                <h1 className={styles.heading}>Classes</h1>
                    <p className={styles.subheading}>
                        Browse courses by level. Pick a bubble to see what's inside.
                    </p>
            </header>
                {groupedClasses.map((group) => (
                    <ClassCloud key={group.key} label={group.label} items={group.items} />
                ))}
        </div>
    );
}

function ClassCloud({ label, items }: {label:string; items: ClassInfo[]}) {
    const  positions = useMemo(
        () => scatterBubbles(items.length, BUBBLE_SIZE_PERCENT),
        [items.length]
    );

    return (
        <section className={styles.cloud}>
            <h2 className={styles.cloudLabel}>{label}</h2>
            <div className={styles.cloudField}>
                {items.map((course, i) => (
                    <Link
                        key={course.id}
                        to={`/classes/${course.code.replace(/\s+/g, '-').toLowerCase()}`}
                        className={styles.bubble}
                        style={{
                            left: `${positions[i].left}%`,
                            top: `${positions[i].top}%`,
                            width: `${BUBBLE_SIZE_PERCENT}%`,
                        }}
                    >
                        <span className={styles.bubbleDrift}>
                            <span
                                className={`${styles.bubbleInner} ${
                                    course.type === 'lab' ? styles.bubbleLab : styles.bubbleLecture
                                }`}
                            >
                                {course.type === 'lab' && (
                                    <svg
                                        className={styles.labBadge}
                                        viewBox="0 0 24 24"
                                        aria-hidden="true"
                                    >
                                        <path
                                            d="M9 2h6M10 2v6.5L4.5 18a2 2 0 0 0 1.8 3h11.4a2 2 0 0 0 1.8-3L14 8.5V2"
                                            fill="none"
                                            stroke="currentColor"
                                            strokeWidth="1.5"
                                            strokeLinecap="round"
                                            strokeLinejoin="round"
                                        />
                                    </svg>
                                )}
                                <span className={styles.bubbleCode}>{course.code}</span>
                                <span className={styles.bubbleTitle}>{course.title}</span>
                            </span>
                        </span>
                    </Link>
                ))}
            </div>
        </section>
    );
}
