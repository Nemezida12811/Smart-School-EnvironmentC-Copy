import './buttons.css';

type BigButtonProps = {
    text: string;
    onClick?: () => void;
};

function BigButton({ text, onClick }: BigButtonProps) {
    return (
        <button onClick={onClick} className="big-button">
            {text}
        </button>
    );
}

export default BigButton;