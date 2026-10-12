import { useParams } from 'react-router-dom';

export default function ClassDetail() {
    const { classCode } = useParams();

    return (
        <div style={{ padding: '64px 32px' }}>
            <h1>{classCode?.toUpperCase().replace(/-/g, ' ')}</h1>
            <p>Class detail content coming soon.</p>
        </div>
    );
}