import {
    useEffect,
    useState
} from "react";


import api from "../../api/axios";


import type {
    CandidateDetailType
} from "../../types/candidate";



interface CommentType {

    id:number;

    author:string;

    role:string;

    comment:string;

    created_at:string;

}




interface Props {

    candidate: CandidateDetailType;

    onUpdate?:()=>void;

}






function CommentSection({

    candidate,

    onUpdate

}:Props){



    const [

        comments,

        setComments

    ] = useState<CommentType[]>([]);




    const [

        text,

        setText

    ] = useState("");




    const [

        loading,

        setLoading

    ] = useState(false);






    async function fetchComments(){


        try{


            const res = await api.get(

                `/candidates/${candidate.candidate_id}/comments`

            );


            setComments(
                res.data.data ?? []
            );


        }

        catch(error){

            console.error(error);

        }


    }







    useEffect(()=>{

        fetchComments();

    },[]);








    async function addComment(){


        if(!text.trim()) return;



        try{


            setLoading(true);



            await api.post(

                `/candidates/${candidate.candidate_id}/comments`,

                {

                    comment:text,

                    role:"HR",

                    author:"HR Admin"

                }

            );



            setText("");



            await fetchComments();



            if(onUpdate){

                onUpdate();

            }


        }

        catch(error){

            console.error(error);

        }

        finally{

            setLoading(false);

        }


    }







    return (

        <section

            className="
            bg-white
            border
            rounded-2xl
            p-5
            "

        >



            {/* HEADER */}


            <div

                className="
                mb-5
                "

            >

                <h2

                    className="
                    text-sm
                    font-bold
                    text-gray-900
                    uppercase
                    "

                >

                    Recruitment Collaboration & Feedback

                </h2>



                <p

                    className="
                    text-xs
                    text-gray-400
                    mt-1
                    "

                >

                    Comments and feedback history

                </p>


            </div>









            {/* COMMENT LIST */}


            <div

                className="
                space-y-5
                mb-6
                "

            >


                {

                comments.length > 0

                ?

                comments.map(comment=>(


                    <div

                        key={comment.id}

                        className="
                        border-l-2
                        border-blue-200
                        pl-4
                        "

                    >


                        <div

                            className="
                            flex
                            justify-between
                            "

                        >

                            <div>


                                <p

                                    className="
                                    text-sm
                                    font-semibold
                                    text-gray-800
                                    "

                                >

                                    {comment.author}

                                </p>



                                <p

                                    className="
                                    text-xs
                                    text-gray-400
                                    "

                                >

                                    {comment.role}

                                </p>


                            </div>





                            <p

                                className="
                                text-xs
                                text-gray-400
                                "

                            >

                                {
                                    new Date(
                                        comment.created_at
                                    )
                                    .toLocaleString(
                                        "en-GB",
                                        {
                                            dateStyle:"medium",
                                            timeStyle:"short"
                                        }
                                    )
                                }

                            </p>


                        </div>






                        <p

                            className="
                            mt-2
                            text-sm
                            text-gray-600
                            leading-6
                            "

                        >

                            {comment.comment}

                        </p>



                    </div>


                ))


                :


                <p

                    className="
                    text-sm
                    text-gray-400
                    "

                >

                    No comments yet

                </p>


                }


            </div>









            {/* ADD COMMENT */}


            <div>


                <textarea


                    value={text}


                    onChange={

                        e=>setText(
                            e.target.value
                        )

                    }


                    rows={4}


                    maxLength={500}


                    placeholder="Add feedback..."


                    className="
                    w-full
                    border
                    border-gray-200
                    rounded-xl
                    p-3
                    text-sm
                    resize-none
                    focus:outline-none
                    focus:ring-2
                    focus:ring-blue-200
                    "

                />




                <div

                    className="
                    flex
                    justify-between
                    items-center
                    mt-2
                    "

                >


                    <span

                        className="
                        text-xs
                        text-gray-400
                        "

                    >

                        {text.length}/500

                    </span>





                    <button


                        disabled={loading}


                        onClick={addComment}


                        className="
                        px-4
                        py-2
                        rounded-xl
                        bg-blue-600
                        text-white
                        text-sm
                        hover:bg-blue-700
                        disabled:opacity-50
                        "

                    >

                        {
                            loading
                            ?
                            "Adding..."
                            :
                            "Add Comment"
                        }


                    </button>



                </div>



            </div>






        </section>

    );

}



export default CommentSection;