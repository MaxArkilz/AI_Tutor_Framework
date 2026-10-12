import { useEffect, useRef, useState } from "react";
import styles from '../CSSModules/base.module.css';

interface ChatMessage {
    id: string;
    sender: 'user' | 'earl';
    text: string;
}

const STORAGE_KEY = 'earl-chat-history';

function loadMessages(): ChatMessage[] {
    try {
        const raw = sessionStorage.getItem(STORAGE_KEY);
        return raw ? JSON.parse(raw) : [];
    } catch {
        return [];
    }
}

export default function EarlModal() {
    const [isOpen, setIsOpen] = useState(false);
    const [messages, setMessages] = useState<ChatMessage[]>(loadMessages);
    const [draft, setDraft] = useState('');
    const scrollRef = useRef<HTMLDivElement>(null);

    // persist messages
    useEffect(() => {
        sessionStorage.setItem(STORAGE_KEY, JSON.stringify(messages));
    }, [messages]);

    // auto-scroll to latest message
    useEffect(() => {
        scrollRef.current?.scrollTo({top: scrollRef.current.scrollHeight, behavior: 'smooth'});
        }, [messages, isOpen]);

    const sendMessage = () => {
        const text = draft.trim();
        if (!text) return;

        const userMsg: ChatMessage = {id: crypto.randomUUID(), sender: 'user', text};
        setMessages((prev) => [...prev, userMsg]);
        setDraft('');

        // TODO: replace w/ real API call later
        setTimeout(() => {
            const earlMsg: ChatMessage = {
                id: crypto.randomUUID(),
                sender: 'earl',
                text: 'Thanks for the message! Tell the dev team to wire up my brain please.'
            };
            setMessages((prev) => [...prev, earlMsg]);
        }, 500);
    };

    const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
        if (e.key === 'Enter') sendMessage();
    };

    return (
        <div className={styles.container}>
            {isOpen && (
                <div className={styles.chatWindow}>
                    <div className={styles.header}>
                        <img src="/Earl.png" alt="Earl Icon" className={styles.headerLogo} />
                        <span className={styles.headerTitle}>Earl</span>
                        <button
                            className={styles.closeButton}
                            onClick={() => setIsOpen(false)}
                            aria-label="Close chat"
                            >
                            X
                        </button>
                    </div>

                    <div className={styles.messages} ref={scrollRef}>
                        {messages.length === 0 && (
                            <div className={styles.emptyState}>Say hi to Earl!</div>
                        )}
                        {messages.map((msg) => (
                            <div
                                key={msg.id}
                                className={`${styles.bubble} ${msg.sender === 'user' ? styles.userBubble : styles.earlBubble}`}>
                                {msg.text}
                            </div>
                        ))}
                    </div>

                    <div className={styles.inputRow}>
                        <input
                            className={styles.input}
                            type='text'
                            placeholder="Type a message..."
                            value={draft}
                            onChange={(e) => setDraft(e.target.value)}
                            onKeyDown={handleKeyDown}
                        />
                        <button className={styles.sendButton} onClick={sendMessage}>
                            Send
                        </button>
                    </div>
                </div>

            )}

            <button
                className={styles.bubbleButton}
                onClick={() => setIsOpen((prev) => !prev)}
                aria-label="Toggle Earl Chat"
                >
                <img src="/Earl.png" alt="Earl Icon" className={styles.logo} />
            </button>
        </div>
    );
}