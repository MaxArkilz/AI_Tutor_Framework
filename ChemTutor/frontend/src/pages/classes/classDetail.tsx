import { useParams } from 'react-router-dom';
import { useTitle } from '../../hooks/useTitle';

export default function ClassDetail() {
    const { classCode } = useParams();
    useTitle(`${classCode?.toUpperCase() ?? 'Class'} | Chem Tutor`);

    return (
        <div style={{ padding: '64px 32px' }}>
            <h1>{classCode?.toUpperCase().replace(/-/g, ' ')}</h1>
            <p>Class detail content coming soon.</p>
        </div>
    );
}