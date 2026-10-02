import './buttons.css';
import plusIcon from '../assets/plus.svg';
import arrowIcon from '../assets/arrow.svg';
import pencilIcon from '../assets/pencil.svg';
import crossIcon from '../assets/cross.svg';

type SmallButtonProps = {
    text: string;
    onClick?: () => void;
    image?: "plus" | "pencil" | "arrow" | "cross"
};

function SmallButton({ text, onClick, image }: SmallButtonProps) {
    return (
        <button onClick={onClick} className="small-button">
            {image == "plus" && <img src={plusIcon} alt="plus"/>}
            {image == "pencil" && <img src={pencilIcon} alt="pencil"/>}
            {image == "cross" && <img src={crossIcon} alt="cross"/>}
            {text}
            {image == "arrow" && <img src={arrowIcon} alt="arrow"/>}
        </button>
    );
}

export default SmallButton;